from apiflask import HTTPError

class BusinessError(HTTPError):
    def __init__(self, message, status_code=400, payload=None):
        super().__init__(status_code, message, payload)

class StaleDataError(BusinessError):
    def __init__(self, message='Data is stale, please refresh', status_code=409):
        super().__init__(message, status_code)
