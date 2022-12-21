import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

import exceptions as ex

load_dotenv()


PRACTICUM_TOKEN = os.getenv('P_TOKEN')
TELEGRAM_TOKEN = os.getenv('TG_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TG_ID')
RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens() -> bool:
    """
    Проверяет доступность переменных окружения,
    которые необходимы для работы программы.
    """
    for key in (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, ENDPOINT):
        if key is None:
            logging.critical(ex.GLOBAL_VARIABLE_IS_MISSING)
            return False
        if not key:
            logging.critical(ex.GLOBAL_VARIABLE_IS_EMPTY)
            return False
    return True


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляет сообщение пользователю в Телегу."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logging.error('Ошибка отправки сообщения!')
        raise ex.MessageSendingError(ex.FAILURE_TO_SEND_MESSAGE.format(
            error=error,
            message=message,
        ))
    logging.debug(f'Сообщение "{message}" отправлено.')


def get_api_answer(current_timestamp: int) -> dict:
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    all_params = dict(url=ENDPOINT, headers=HEADERS, params=params)
    try:
        response = requests.get(**all_params)
    except requests.exceptions.RequestException as error:
        raise telegram.TelegramError(ex.CONNECTION_ERROR.format(
            error=error,
            **all_params,
        ))
    response_status = response.status_code
    if response_status != 200:
        raise ex.EndpointError(ex.WRONG_ENDPOINT.format(
            response_status=response_status,
            **all_params,
        ))
    try:
        return response.json()
    except Exception as error:
        raise ex.ResponseFormatError(ex.FORMAT_NOT_JSON.format(error))


def check_response(response: dict) -> list:
    """
    Возвращает домашку, если есть.
    Проверяет валидность её статуса.
    """
    logging.info('Проверка ответа API на корректность')
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является dict')
    if 'homeworks' not in response or 'current_date' not in response:
        raise ex.EmptyResponseFromAPI('Нет ключа homeworks в ответе API')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('homeworks не является list')
    return response['homeworks'][0]


def parse_status(homework: dict) -> str:
    """Возвращает вердикт ревьюера."""
    logging.info('Проводим проверки и извлекаем статус работы')
    if 'homework_name' not in homework:
        raise KeyError('Нет ключа homework_name в ответе API')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неизвестный статус работы - {homework_status}')
    return ('Изменился статус проверки работы "{homework_name}". {verdict}'
            ).format(homework_name=homework_name,
                     verdict=HOMEWORK_VERDICTS[homework_status]
                     )


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise ex.GlobalsError('Ошибка глобальной переменной. Смотри логи.')
    current_timestamp = int(time.time())
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)
            logging.info(homework)
            current_timestamp = response.get('current_date')
        except IndexError:
            message = 'Статус работы не изменился'
            send_message(bot, message)
            logging.info(message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)
        logging.info(ex.MESSAGE_IS_SENT.format(message))


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.FileHandler(
                os.path.abspath('main.log'), mode='a', encoding='UTF-8'),
            logging.StreamHandler(stream=sys.stdout)],
        format='%(asctime)s, %(levelname)s,'
               '%(name)s, %(message)s'
    )
    main()
