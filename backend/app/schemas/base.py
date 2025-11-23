from apiflask import Schema
from apiflask.fields import Integer, String, Field

class BaseResponseSchema(Schema):
    code = Integer(dump_default=0, metadata={'description': 'Business Code (0 for success)'})
    message = String(dump_default='success', metadata={'description': 'Response Message'})
    data = Field(metadata={'description': 'Response Data Payload'})

