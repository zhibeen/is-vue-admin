from flask import render_template
from weasyprint import HTML

class PDFService:
    def generate_supplier_contract_pdf(self, supplier_name, contracts):
        """
        生成单个供应商的合同集合 PDF（每份合同一页，或连续打印）
        """
        # 渲染 HTML 模板
        html_content = render_template(
            'pdf/contract_batch.html',
            supplier_name=supplier_name,
            contracts=contracts
        )
        # 转为 PDF 二进制
        return HTML(string=html_content).write_pdf()

pdf_service = PDFService()

