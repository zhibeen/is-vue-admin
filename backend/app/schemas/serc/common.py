from apiflask import Schema
from apiflask.fields import Integer, String, Integer

class PaymentTermSchema(Schema):
    id = Integer()
    code = String(metadata={'description': '代码 (NET30)'})
    name = String(metadata={'description': '名称 (月结30天)'})
    baseline = String(metadata={'description': '基准日'})
    days_offset = Integer(metadata={'description': '偏移天数'})

