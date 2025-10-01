class AppExceptionCase(Exception):
    """Custom exception class for application-specific errors."""
    
    def __init__(self, status_code: int, context: dict):
        self.exception_case = self.__class__.__name__
        self.status_code = status_code
        self.context = context

    def __str__(self):
        return (
            f"<AppException {self.exception_case} - "
            + f"status_code={self.status_code} - context={self.context}>"
        )
    
class AppException(object):
    class BadRequest(AppExceptionCase):
        def __init__(self, context: dict = {}):
            """Invalid or malformed request."""
            status_code = 400
            AppExceptionCase.__init__(self, status_code, context)

    class UnprocessableEntity(AppExceptionCase):
        def __init__(self, context=None):
            """lists all syntax and parameter violations in the response."""
            status_code = 422
            AppExceptionCase.__init__(self, status_code, context)

    class TooManyRequests(AppExceptionCase):
        def __init__(self, context=None):
            """Rate limit hit"""
            status_code = 429
            AppExceptionCase.__init__(self, status_code, context)
