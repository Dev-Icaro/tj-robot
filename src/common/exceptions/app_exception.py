class AppException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class RequiredArgumentException(AppException):
    def __init__(self, message):
        super().__init__(message)


class InvalidArgumentException(AppException):
    def __init__(self, message):
        super().__init__(message)


class InvalidDateException(AppException):
    def __init__(self, message):
        super().__init__(message)
