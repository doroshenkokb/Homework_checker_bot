import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

import exceptions as ex
import errorsmessage as er

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
    """Проверяет доступность переменных окружения."""
    env_variables = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    no_value = [
        var_name for var_name, value in env_variables.items() if not value
    ]
    if no_value:
        logging.critical(f'{er.GLOBAL_VARIABLE_IS_MISSING} {no_value}')
        return False
    return True


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляет сообщение пользователю в Телегу."""
    try:
        logging.info('Начало отправки сообщения')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logging.error(er.FAILURE_TO_SEND_MESSAGE)
        raise ex.MessageSendingError(er.FAILURE_TO_SEND_MESSAGE.format(
            error=error,
            message=message,
        ))
    logging.debug('Успешная отправка сообщения')


def get_api_answer(current_timestamp: int) -> dict:
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    all_params = dict(url=ENDPOINT, headers=HEADERS, params=params)
    try:
        response = requests.get(**all_params)
        logging.info('Делаем запрос к единственному эндпоинту')
    except requests.exceptions.RequestException as error:
        raise ex.ConnectionError(er.CONNECTION_ERROR.format(
            error=error,
            **all_params,
        ))
    response_status = response.status_code
    if response_status != 200:
        raise ex.WrongResponseCode(
            f'{ENDPOINT} с заданными параметрами недоступен'
        )
    try:
        return response.json()
    except Exception as error:
        raise ex.ResponseFormatError(er.FORMAT_NOT_JSON.format(error))


def check_response(response: dict) -> list:
    """
    Возвращает домашку, если есть.
    Проверяет валидность её статуса.
    """
    logging.info('Проверка ответа API на корректность')
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является dict')
    elif 'homeworks' not in response or 'current_date' not in response:
        raise ex.EmptyResponseFromAPI('Нет ключа homeworks в ответе API')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('homeworks не является list')
    elif not homeworks:
        logging.debug(
            'Статус проверки домашнего задания не обновлялся'
        )
        return homeworks
    return homeworks


def parse_status(homework: dict) -> str:
    """Возвращает вердикт ревьюера."""
    logging.info('Проверка статуса работы')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    for key in ('homework_name', 'status'):
        if key not in homework:
            raise KeyError(
                'Отсутствует необходимый ключ для определения статуса '
                f'проверки домашнего задания: {key}'
            )
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неизвестный статус работы - {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}": {verdict}'


def main(): # noqa: max-complexity: 13
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit()
    current_timestamp = int(time.time())
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    new_message = ''
    hw_dict = {}
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            current_timestamp = response.get('current_date', current_timestamp)
            num_works = len(homeworks)
            if num_works > 0:
                for homework in homeworks:
                    name = homework.get('homework_name')
                    status = homework.get('status')
                    if name not in hw_dict.keys():
                        hw_dict[name] = status
                        message = parse_status(homework)
                        send_message(bot, message)
                        hw_dict = hw_dict
                    else:
                        if status != hw_dict[name]:
                            hw_dict[name] = status
                            message = parse_status(homework)
                            send_message(bot, message)
            time.sleep(RETRY_PERIOD)
        except ex.MessageSendingError as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=True)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message not in new_message:
                new_message = message
                logging.error(message, exc_info=True)
                send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.FileHandler(
                os.path.abspath(
                    'main.log'
                ),
                mode='a',
                encoding='UTF-8'
            ),
            logging.StreamHandler(
                stream=sys.stdout
            )
        ],
        format='%(asctime)s, %(levelname)s,'
               '%(name)s, %(message)s'
    )
    main()
