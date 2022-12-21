class EmptyResponseFromAPI(Exception):
    """"В ответе API домашки нет ключа `homeworks`."""

    pass


class EndpointError(Exception):
    """Ошибка, если эндпойнт не корректен."""

    pass


class MessageSendingError(Exception):
    """Ошибка отправки сообщения."""

    pass


class GlobalsError(Exception):
    """Ошибка, если есть пустые глобальные переменные."""

    pass


class ResponseFormatError(Exception):
    """Ошибка, если формат response не json."""

    pass


CONNECTION_ERROR = '{error}, {url}, {headers}, {params}'
WRONG_ENDPOINT = '{response_status}, {url}, {headers}, {params}'
FAILURE_TO_SEND_MESSAGE = '{error}, {message}'
GLOBAL_VARIABLE_IS_MISSING = 'Отсутствует глобальная переменная'
GLOBAL_VARIABLE_IS_EMPTY = 'Пустая глобальная переменная'
MESSAGE_IS_SENT = 'Сообщение {message} отправлено'
FORMAT_NOT_JSON = 'Формат не json {error}'
LIST_IS_EMPTY = 'Список пустой'
