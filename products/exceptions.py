class CoreException(Exception):
    def __init__(self, message, *args, details=None):
        self.message = message % args
        self.details = details
        super().__init__(args)

    def __str__(self):
        return self.message


class SpiderDoesNotExist(CoreException):
    def __init__(self, spider_name):
        super().__init__('Spider `%s` does not exist.', spider_name)


class SpiderAlreadyStarted(CoreException):
    def __init__(self, spider_name):
        super().__init__('Spider `%s` already started.', spider_name)


class SpiderNotRunning(CoreException):
    def __init__(self, spider_name):
        super().__init__('Spider `%s` is not running.', spider_name)


class SpiderStopPhantom(CoreException):
    def __init__(self, spider_name):
        super().__init__('Spider `%s` already received stop signal. Waiting for graceful shutdown.', spider_name)


class ValidationError(CoreException):
    def __init__(self, message, *args, details):
        super().__init__(message, *args, details=details)
