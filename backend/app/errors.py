from apiflask import HTTPError
from app import codes

class BusinessError(HTTPError):
    def __init__(self, message, code=codes.BAD_REQUEST, status_code=400, data=None):
        """
        :param message: 错误提示信息
        :param code: 业务状态码 (从 app.codes 引用)
        :param status_code: HTTP 状态码 (默认 400)
        :param data: 附加数据 (会放入响应的 data 字段中)
        """
        # APIFlask uses 'extra_data' to add fields to the response body
        extra_data = {
            'code': code,
            'data': data
        }
        super().__init__(status_code, message, extra_data)
        self.code = code
        self.data = data

class StaleDataError(BusinessError):
    def __init__(self, message='Data is stale, please refresh', status_code=409):
        super().__init__(message, code=codes.STALE_DATA_ERROR, status_code=status_code)
