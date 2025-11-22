from apiflask import HTTPError

class BusinessError(HTTPError):
    def __init__(self, message, status_code=400, payload=None):
        super().__init__(status_code, message, payload)

