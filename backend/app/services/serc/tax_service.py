from typing import List, Dict, Optional, Tuple
from sqlalchemy import select, desc
from app.extensions import db
from app.models.serc.tax import TaxInvoice, TaxInvoiceItem
from app.models.serc.enums import TaxInvoiceStatus

class TaxService:
    def get_invoices(self, page: int, per_page: int, filters: Dict = None):
        stmt = select(TaxInvoice).order_by(desc(TaxInvoice.created_at))
        # Filters...
        pagination = db.paginate(stmt, page=page, per_page=per_page)
        return pagination

    # TODO: Add Invoice creation / management methods here

tax_service = TaxService()
