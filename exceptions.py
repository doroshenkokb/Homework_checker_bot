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


class  WrongResponseCode(Exception):
    """Ответ API не возвращает 200."""

    pass


class ConnectionError(Exception):
    """Oшибка соединения"""
    pass
