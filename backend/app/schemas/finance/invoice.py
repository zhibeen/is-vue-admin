"""供应商发票相关Schemas"""
from apiflask import Schema
from apiflask.fields import String, Integer, Float, Date, DateTime


class SupplierTaxInvoiceSchema(Schema):
    """供应商发票Schema（输出）"""
    id = Integer(dump_only=True)
    invoice_no = String(required=True, metadata={'description': '发票号码', 'example': 'INV-2024-001'})
    invoice_code = String(required=True, metadata={'description': '发票代码'})
    
    # 关联信息
    supply_contract_id = Integer(
        required=True,
        metadata={'description': '关联开票合同ID'}
    )
    supplier_id = Integer(required=True, metadata={'description': '供应商ID'})
    
    # 金额信息
    amount = Float(required=True, metadata={'description': '不含税金额'})
    tax_amount = Float(required=True, metadata={'description': '税额'})
    total_amount = Float(required=True, metadata={'description': '价税合计'})
    
    # 发票类型
    invoice_type = String(metadata={'description': '发票类型: special/ordinary/electronic'})
    
    # 状态
    status = String(metadata={'description': '状态: valid/cancelled/invalid'})
    
    # 日期信息
    invoice_date = Date(required=True, metadata={'description': '开票日期'})
    received_date = Date(metadata={'description': '收票日期'})
    
    # 附件
    attachment_url = String(metadata={'description': '发票扫描件URL'})
    
    # 审计字段
    created_at = DateTime(dump_only=True)
    updated_at = DateTime(dump_only=True)
    created_by = Integer(dump_only=True)


class SupplierTaxInvoiceCreateSchema(Schema):
    """供应商发票创建Schema"""
    invoice_no = String(required=True, metadata={'description': '发票号码'})
    invoice_code = String(required=True, metadata={'description': '发票代码'})
    
    # 关联信息
    supply_contract_id = Integer(
        required=True,
        metadata={'description': '关联开票合同ID'}
    )
    supplier_id = Integer(required=True, metadata={'description': '供应商ID'})
    
    # 金额信息
    amount = Float(required=True, metadata={'description': '不含税金额'})
    tax_amount = Float(required=True, metadata={'description': '税额'})
    total_amount = Float(required=True, metadata={'description': '价税合计'})
    
    # 发票类型
    invoice_type = String(
        required=True,
        metadata={'description': '发票类型: special/ordinary/electronic', 'example': 'special'}
    )
    
    # 日期信息
    invoice_date = Date(required=True, metadata={'description': '开票日期'})
    received_date = Date(metadata={'description': '收票日期'})
    
    # 附件
    attachment_url = String(metadata={'description': '发票扫描件URL'})

