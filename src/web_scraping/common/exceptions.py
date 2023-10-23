from common.exceptions.app_exception import AppException


class InvalidPageException(AppException):
    def __init__(self, message):
        super().__init__(message)


class DisabledCalendarDateException(AppException):
    def __init__(self, message):
        super().__init__(message)
