from apiflask import APIBlueprint, Schema
from apiflask.fields import Integer, String, List, Float, Boolean, Decimal as DecimalField, Nested
from app.services.serc.finance_service import finance_service
from app.extensions import db
from app.models.serc.finance import FinSupplyContract
from apiflask.views import MethodView

bp = APIBlueprint('finance_supply', __name__, url_prefix='/finance/supply-contracts', tag='L1.5 供货合同')

# --- Schemas ---

class SupplyContractItemSchema(Schema):
    invoice_name = String(required=True)
    invoice_unit = String()
    specs = String()
    quantity = DecimalField(required=True)
    price_unit = DecimalField(required=True)
    amount = DecimalField(required=True)
    tax_rate = DecimalField(required=True)
    tax_code = String()
    skus = List(String())

class PreviewResponseSchema(Schema):
    l1_contract_id = Integer()
    contract_no = String()
    supplier_name = String()
    l1_total_amount = DecimalField()
    preview_total_amount = DecimalField()
    diff = DecimalField()
    is_balanced = Boolean()
    items = List(Nested(SupplyContractItemSchema))
    warnings = List(String())

class GenerateRequestSchema(Schema):
    l1_contract_id = Integer(required=True)
    confirmed_items = List(Nested(SupplyContractItemSchema), required=True)

class SupplyContractResponseSchema(Schema):
    id = Integer()
    contract_no = String()
    status = String()
    total_amount = DecimalField()

# --- Views ---

@bp.route('/preview/<int:l1_id>')
class PreviewSupplyContractAPI(MethodView):
    @bp.output(PreviewResponseSchema)
    def get(self, l1_id):
        """预览 L1.5 合同生成结果"""
        return finance_service.preview_supply_contract_from_l1(l1_id)

@bp.route('/generate')
class GenerateSupplyContractAPI(MethodView):
    @bp.input(GenerateRequestSchema, arg_name='data')
    @bp.output(SupplyContractResponseSchema)
    def post(self, data):
        """正式生成 L1.5 合同"""
        contract = finance_service.create_supply_contract_from_l1(
            data['l1_contract_id'], 
            data['confirmed_items']
        )
        return {
            'data': {
                'id': contract.id, 
                'contract_no': contract.contract_no,
                'status': contract.status,
                'total_amount': contract.total_amount
            }
        }

