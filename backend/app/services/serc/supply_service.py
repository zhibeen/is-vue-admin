from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, func
from app.extensions import db
from app.models.supply import ScmDeliveryContract, ScmDeliveryContractItem, ScmSourceDoc, ScmContractChangeLog
from app.models.serc.enums import SourceDocType, ContractStatus
from app.models.purchase.supplier import SysSupplier
from app.models.product import Product
from app.services.serc.common import generate_seq_no
from app.errors import StaleDataError

class SupplyService:
    def create_manual_contract(self, data: dict) -> ScmDeliveryContract:
        """
        手工创建交付合同 (L1)
        逻辑:
        1. 自动创建虚拟 SourceDoc (SourceDocType.GRN_STOCK)
        2. 创建 DeliveryContract
        3. 计算 Item Total & Contract Total
        """
        supplier_id = data['supplier_id']
        event_date = data['event_date']
        items_data = data['items']

        # 0. 校验供应商
        supplier = db.session.get(SysSupplier, supplier_id)
        if not supplier:
            raise ValueError(f"Supplier ID {supplier_id} not found")

        # 0.1 获取采购主体 (公司)
        from app.models.serc.foundation import SysCompany
        company = None
        if 'company_id' in data and data['company_id']:
            company = db.session.get(SysCompany, data['company_id'])
            if not company:
                raise ValueError(f"Company ID {data['company_id']} not found")
        
        company_code = company.code if company else None

        # 逻辑优化：如果前端未传自定义条款，则使用供应商默认值
        payment_terms = data.get('payment_terms') or supplier.payment_terms
        payment_method = data.get('payment_method') or supplier.payment_method

        # 0.2 生成供应商快照 (Snapshot)
        snapshot_data = {
            "id": supplier.id,
            "name": supplier.name,
            "short_name": supplier.short_name,
            "tax_id": supplier.tax_id,
            "payment_terms": payment_terms,
            "payment_method": payment_method,
            "bank_accounts": supplier.bank_accounts
        }

        # 1. 生成单号
        # 虚拟源头单号: VGRN-2311-0001
        source_doc_no = generate_seq_no("VGRN", company_code)
        # 合同单号: SZ-L1-2311-0001
        contract_no = generate_seq_no("L1", company_code)

        # 2. 创建虚拟源头单据 (SourceDoc)
        # 手工录入被视为一种“虚拟入库”
        source_doc = ScmSourceDoc(
            doc_no=source_doc_no,
            type=SourceDocType.GRN_STOCK.value,
            supplier_id=supplier_id,
            event_date=event_date,
            tracking_source={"type": "manual_entry"}
        )
        db.session.add(source_doc)
        db.session.flush()  # 获取 ID

        # 3. 创建 L1 合同主体
        contract = ScmDeliveryContract(
            contract_no=contract_no,
            source_doc_id=source_doc.id,
            supplier_id=supplier_id,
            company_id=company.id if company else None, # 保存采购主体 ID
            currency=data.get('currency', 'CNY'),
            
            # Added fields
            delivery_address=data.get('delivery_address'),
            delivery_date=data.get('delivery_date'),
            notes=data.get('notes'),
            
            # 保存付款信息
            payment_terms=payment_terms,
            payment_method=payment_method,
            
            # 保存快照
            supplier_snapshot=snapshot_data,

            status=ContractStatus.PENDING.value,
            total_amount=Decimal("0.00")
        )
        db.session.add(contract)
        db.session.flush()

        # 4. 处理明细并计算总价
        total_amount = Decimal("0.00")
        
        for item_data in items_data:
            product_id = item_data['product_id']
            qty = Decimal(str(item_data['confirmed_qty']))
            price = Decimal(str(item_data['unit_price']))
            notes = item_data.get('notes', '')
            
            # 校验商品是否存在
            product = db.session.get(Product, product_id)
            if not product:
                raise ValueError(f"Product ID {product_id} not found")
                
            line_total = qty * price
            total_amount += line_total
            
            item = ScmDeliveryContractItem(
                l1_contract_id=contract.id,
                product_id=product_id,
                confirmed_qty=qty,
                unit_price=price,
                total_price=line_total,
                notes=notes
            )
            db.session.add(item)

        # 5. 回写总金额
        contract.total_amount = total_amount
        
        db.session.commit()
        return contract

    def get_contract_list(self, page=1, per_page=20, filters=None):
        # 预加载 supplier, company, items, source_doc 避免 N+1
        from sqlalchemy.orm import selectinload
        query = select(ScmDeliveryContract).options(
            selectinload(ScmDeliveryContract.supplier),
            selectinload(ScmDeliveryContract.company),
            selectinload(ScmDeliveryContract.items),
            selectinload(ScmDeliveryContract.source_doc)
        ).order_by(ScmDeliveryContract.id.desc())
        
        if filters:
            if filters.get('contract_no'):
                query = query.filter(ScmDeliveryContract.contract_no.ilike(f"%{filters['contract_no']}%"))
            if filters.get('supplier_id'):
                query = query.filter(ScmDeliveryContract.supplier_id == filters['supplier_id'])
            if filters.get('company_id'):
                query = query.filter(ScmDeliveryContract.company_id == filters['company_id'])
            if filters.get('status'):
                query = query.filter(ScmDeliveryContract.status == filters['status'])
        
        return db.paginate(query, page=page, per_page=per_page)

    def update_contract(self, contract_id: int, data: dict, user_id: int = None) -> ScmDeliveryContract:
        """
        更新合同 (带乐观锁和变更记录)
        """
        contract = db.session.get(ScmDeliveryContract, contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")
            
        # 1. 乐观锁检查 (Optimistic Locking)
        # 前端必须传递当前的版本号
        request_version = data.get('version')
        if request_version is not None and int(request_version) != contract.version:
            raise StaleDataError(f"数据版本不一致 (Client: {request_version}, Server: {contract.version})，请刷新后重试")
            
        # 2. 准备变更日志 (Snapshot Before)
        old_snapshot = self._serialize_contract(contract)
        
        # 3. 更新字段
        if 'notes' in data:
            contract.notes = data['notes']
        if 'delivery_date' in data:
            contract.delivery_date = data['delivery_date']
        if 'delivery_address' in data:
            contract.delivery_address = data['delivery_address']
        if 'payment_terms' in data:
            contract.payment_terms = data['payment_terms']
        if 'payment_method' in data:
            contract.payment_method = data['payment_method']
            
        # 4. 更新明细 (Items)
        # 如果传入了 items 数组，则视为全量替换 (简化逻辑)
        if 'items' in data:
            # 清除旧明细 (ORM会自动处理 orphan delete吗？如果不配置 delete-orphan，需要手动删)
            # 在 Model 配置了 cascade="all, delete-orphan"，所以直接清空 list 即可
            contract.items = [] 
            
            total_amount = Decimal("0.00")
            for item_data in data['items']:
                product_id = item_data['product_id']
                qty = Decimal(str(item_data['confirmed_qty']))
                price = Decimal(str(item_data['unit_price']))
                
                line_total = qty * price
                total_amount += line_total
                
                item = ScmDeliveryContractItem(
                    product_id=product_id,
                    confirmed_qty=qty,
                    unit_price=price,
                    total_price=line_total,
                    notes=item_data.get('notes', '')
                )
                contract.items.append(item)
            
            contract.total_amount = total_amount
            
        # 5. 更新版本号
        contract.version += 1
        
        # 6. 记录日志 (Snapshot After)
        # 注意：这里需要在 commit 前获取新状态。对于关联对象，可能需要 flush。
        # 但我们不需要获取 ID，只需要数据。
        new_snapshot = self._serialize_contract(contract)
        
        change_log = ScmContractChangeLog(
            contract_id=contract.id,
            changed_by=user_id,
            change_type='update',
            change_reason=data.get('change_reason', 'Manual Update'),
            content_before=old_snapshot,
            content_after=new_snapshot
        )
        db.session.add(change_log)
        
        db.session.commit()
        return contract

    def _serialize_contract(self, contract):
        """序列化合同关键信息用于快照"""
        return {
            "contract_no": contract.contract_no,
            "total_amount": str(contract.total_amount),
            "status": contract.status,
            "version": contract.version,
            "delivery_date": str(contract.delivery_date) if contract.delivery_date else None,
            "notes": contract.notes,
            "items": [
                {
                    "product_id": i.product_id, 
                    "qty": str(i.confirmed_qty), 
                    "price": str(i.unit_price)
                }
                for i in contract.items
            ]
        }

supply_service = SupplyService()
