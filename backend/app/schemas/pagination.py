from apiflask import Schema
from apiflask.fields import Integer, List, Nested, Boolean, String

class PaginationQuerySchema(Schema):
    page = Integer(load_default=1)
    per_page = Integer(load_default=20)
    # Common filters
    q = String(load_default=None, metadata={'description': '通用搜索关键词 (模糊匹配)'})
    sort = String(load_default='id', metadata={'description': '排序字段 (e.g. id, -created_at)'})

class PaginationSchema(Schema):
    page = Integer()
    per_page = Integer()
    total = Integer()
    pages = Integer()
    
def make_pagination_schema(item_schema):
    class PaginatedResponse(PaginationSchema):
        items = List(Nested(item_schema))
    return PaginatedResponse
