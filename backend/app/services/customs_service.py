from typing import List, Dict, Optional
from sqlalchemy import select, desc, func
from app.extensions import db
from app.models.customs import CustomsDeclaration, CustomsDeclarationItem, CustomsAttachment
from app.models.serc.enums import CustomsStatus, ContractStatus
from app.models.purchase.supplier import SysSupplier
from app.models.supply.delivery import ScmDeliveryContract, ScmDeliveryContractItem
from app.models.product import Product
from app.models.serc.foundation import SysCompany
from app.errors import BusinessError
from app.services.synology_client import SynologyClient
from app.services.serc.common import generate_seq_no
from app.services.customs.status_manager import DeclarationStatusManager, StatusTransitionValidator
from app.services.customs.audit_service import audit_service
import pandas as pd
import datetime
from datetime import datetime as dt
import logging

logger = logging.getLogger(__name__)

class CustomsService:
    def get_declarations(self, page: int, per_page: int, filters: Dict = None):
        stmt = select(CustomsDeclaration).options(
            db.selectinload(CustomsDeclaration.internal_shipper)
        ).order_by(desc(CustomsDeclaration.pre_entry_no))
        
        # Apply filters
        if filters:
            if filters.get('status') and filters['status'] != 'all':
                status_val = filters['status']
                if ',' in status_val:
                    status_list = [s.strip() for s in status_val.split(',') if s.strip()]
                    stmt = stmt.filter(CustomsDeclaration.status.in_(status_list))
                else:
                    stmt = stmt.filter(CustomsDeclaration.status == status_val)
            
            # 编号搜索：支持多字段模糊搜索 (pre_entry_no, customs_no)
            if filters.get('search_no'):
                search_term = f"%{filters['search_no']}%"
                stmt = stmt.filter(
                    db.or_(
                        CustomsDeclaration.pre_entry_no.ilike(search_term),
                        CustomsDeclaration.customs_no.ilike(search_term)
                    )
                )
            
            # 独立的预录入编号搜索
            if filters.get('pre_entry_no'):
                stmt = stmt.filter(CustomsDeclaration.pre_entry_no.ilike(f"%{filters['pre_entry_no']}%"))
            
            if filters.get('container_mode'):
                stmt = stmt.filter(CustomsDeclaration.container_mode == filters['container_mode'])

        pagination = db.paginate(stmt, page=page, per_page=per_page)
        return pagination

    def get_declaration_stats(self) -> List[Dict]:
        """
        获取各状态报关单数量统计
        """
        stmt = select(CustomsDeclaration.status, func.count(CustomsDeclaration.id)).group_by(CustomsDeclaration.status)
        results = db.session.execute(stmt).all()
        
        stats = []
        for status, count in results:
            stats.append({
                'status': status,
                'count': count,
                'label': status 
            })
        return stats

    def get_declaration(self, id: int) -> Optional[CustomsDeclaration]:
        """
        获取报关单详情（预加载关联数据）
        """
        stmt = select(CustomsDeclaration).where(CustomsDeclaration.id == id).options(
            db.selectinload(CustomsDeclaration.items).selectinload(CustomsDeclarationItem.product),
            db.selectinload(CustomsDeclaration.internal_shipper),
            db.selectinload(CustomsDeclaration.creator),
            db.selectinload(CustomsDeclaration.attachments)
        )
        return db.session.execute(stmt).scalar_one_or_none()

    def generate_pre_entry_no(self, internal_shipper_id: int) -> str:
        """
        生成预录入编号
        格式: {COMPANY_CODE}-YL-{YYMM}-{SEQ}
        Example: HR-YL-2412-0001
        
        Args:
            internal_shipper_id: 境内发货人ID
            
        Returns:
            预录入编号字符串
            
        Raises:
            BusinessError: 如果公司不存在或未设置公司代码
        """
        # 获取公司信息
        company = db.session.get(SysCompany, internal_shipper_id)
        if not company:
            raise BusinessError(f"境内发货人 ID {internal_shipper_id} 不存在", code=404)
        
        company_code = company.code
        if not company_code:
            raise BusinessError(
                f"公司 {company.legal_name} 未设置公司代码（code 字段），无法生成预录入编号。"
                "请先在系统设置中为该公司配置公司代码。", 
                code=400
            )
        
        # 调用统一序列号生成器
        # 前缀为 "YL" (预录)，按公司按月隔离
        pre_entry_no = generate_seq_no(prefix="YL", company_code=company_code)
        
        return pre_entry_no

    def create_declaration(self, data: Dict, created_by: int = None) -> CustomsDeclaration:
        # 生成预录入编号（如果有境内发货人且未手动指定）
        pre_entry_no = data.get('pre_entry_no')
        internal_shipper_id = data.get('internal_shipper_id')
        
        if not pre_entry_no and internal_shipper_id:
            try:
                pre_entry_no = self.generate_pre_entry_no(internal_shipper_id)
            except BusinessError:
                # 如果生成失败（比如公司未设置代码），继续创建但不设置预录入编号
                # 这样不会阻止报关单创建，可以后续补充
                pass
        
        # Create Declaration
        decl = CustomsDeclaration(
            pre_entry_no=pre_entry_no,
            internal_shipper_id=internal_shipper_id,
            export_date=data.get('export_date'),
            destination_country=data.get('destination_country'),
            fob_total=data.get('fob_total', 0),
            exchange_rate=data.get('exchange_rate', 1.0),
            
            # Logistics & Source
            logistics_provider=data.get('logistics_provider'),
            bill_of_lading_no=data.get('shipping_no') or data.get('bill_of_lading_no'),
            shipping_date=data.get('shipping_date'),
            source_type=data.get('source_type', 'manual'),
            source_file_url=data.get('source_file_url'),
            container_mode=data.get('container_mode', 'FCL'), # Default to FCL
            
            # 创建人
            created_by=created_by,
            
            status=CustomsStatus.DRAFT.value
        )
        db.session.add(decl)
        db.session.flush()
        
        # 记录审计日志
        audit_service.log_create(decl.id, {
            'pre_entry_no': pre_entry_no,
            'internal_shipper_id': internal_shipper_id,
            'source_type': data.get('source_type', 'manual')
        })

        # Create Items
        for item_data in data.get('items', []):
            item = CustomsDeclarationItem(
                declaration_id=decl.id,
                product_id=item_data['product_id'],
                supplier_id=item_data.get('supplier_id'),
                sku=item_data.get('sku'),
                qty=item_data['qty'],
                unit=item_data['unit'],
                usd_unit_price=item_data['usd_unit_price'],
                usd_total=item_data['usd_total'],
                
                # Packing Info
                box_no=item_data.get('box_no'),
                net_weight=item_data.get('net_weight'),
                gross_weight=item_data.get('gross_weight')
            )
            db.session.add(item)
        
        db.session.commit()
        return decl

    def change_status(self, id: int, new_status: str, reason: Optional[str] = None) -> CustomsDeclaration:
        """
        改变报关单状态（带流转控制）
        
        Args:
            id: 报关单ID
            new_status: 新状态
            reason: 变更原因（可选）
            
        Returns:
            更新后的报关单对象
            
        Raises:
            BusinessError: 不允许的状态转换或前置条件不满足
        """
        decl = db.session.get(CustomsDeclaration, id)
        if not decl:
            raise BusinessError("报关单不存在", code=404)
        
        current_status = decl.status
        
        # 1. 验证状态转换是否允许
        DeclarationStatusManager.validate_transition(current_status, new_status)
        
        # 2. 验证业务前置条件
        if new_status == CustomsStatus.PENDING_REVIEW.value:
            StatusTransitionValidator.validate_submit_for_review(decl)
        elif new_status == CustomsStatus.DECLARED.value:
            StatusTransitionValidator.validate_declare(decl)
        elif new_status == CustomsStatus.CLEARED.value:
            StatusTransitionValidator.validate_cleared(decl)
        elif new_status == CustomsStatus.ARCHIVED.value:
            StatusTransitionValidator.validate_archive(decl)
        
        # 3. 执行状态变更
        old_status = decl.status
        decl.status = new_status
        
        # 4. 更新锁定标志
        decl.is_locked = DeclarationStatusManager.is_locked(new_status)
        
        # 5. 记录变更原因（如果是修撤流程）
        if new_status == CustomsStatus.AMENDING.value and reason:
            decl.amendment_reason = reason
        
        # 6. 审计日志
        audit_service.log_status_change(id, old_status, new_status, reason)
        
        # 7. 应用日志
        logger.info(
            f"Declaration {id} status changed: {old_status} -> {new_status}",
            extra={
                'declaration_id': id,
                'old_status': old_status,
                'new_status': new_status,
                'reason': reason
            }
        )
        
        db.session.commit()
        return decl
    
    def update_declaration_status(self, id: int, status: str):
        """
        @deprecated 使用 change_status 代替
        """
        logger.warning("update_declaration_status is deprecated, use change_status instead")
        return self.change_status(id, status)

    def update_declaration(self, id: int, data: Dict) -> CustomsDeclaration:
        decl = db.session.get(CustomsDeclaration, id)
        if not decl:
            raise BusinessError("Declaration not found", 404)
        
        # 检查锁定状态
        if decl.is_locked and decl.status not in [CustomsStatus.DRAFT.value, CustomsStatus.AMENDMENT_APPROVED.value]:
            raise BusinessError(
                f"报关单当前状态为 '{decl.status}'，已锁定，不允许修改。"
                "如需修改，请申请修撤流程。",
                code=403
            )
            
        # Update basic fields
        if 'internal_shipper_id' in data: decl.internal_shipper_id = data['internal_shipper_id']
        if 'currency' in data: decl.currency = data['currency'] # 新增
        if 'pre_entry_no' in data: decl.pre_entry_no = data['pre_entry_no']
        if 'customs_no' in data: decl.customs_no = data['customs_no']
        if 'entry_port' in data: decl.entry_port = data['entry_port']
        if 'departure_port' in data: decl.departure_port = data['departure_port']
        if 'export_date' in data: decl.export_date = data['export_date']
        if 'declare_date' in data: decl.declare_date = data['declare_date']
        if 'filing_no' in data: decl.filing_no = data['filing_no']
        if 'overseas_consignee' in data: decl.overseas_consignee = data['overseas_consignee']
        if 'transport_mode' in data: decl.transport_mode = data['transport_mode']
        if 'conveyance_ref' in data: decl.conveyance_ref = data['conveyance_ref']
        if 'bill_of_lading_no' in data: decl.bill_of_lading_no = data['bill_of_lading_no']
        if 'trade_mode' in data: decl.trade_mode = data['trade_mode']
        if 'nature_of_exemption' in data: decl.nature_of_exemption = data['nature_of_exemption']
        if 'license_no' in data: decl.license_no = data['license_no']
        if 'contract_no' in data: decl.contract_no = data['contract_no']
        if 'trade_country' in data: decl.trade_country = data['trade_country']
        if 'destination_country' in data: decl.destination_country = data['destination_country']
        if 'loading_port' in data: decl.loading_port = data['loading_port']
        if 'package_type' in data: decl.package_type = data['package_type']
        if 'pack_count' in data: decl.pack_count = data['pack_count']
        if 'gross_weight' in data: decl.gross_weight = data['gross_weight']
        if 'net_weight' in data: decl.net_weight = data['net_weight']
        if 'transaction_mode' in data: decl.transaction_mode = data['transaction_mode']
        if 'freight' in data: decl.freight = data['freight']
        if 'insurance' in data: decl.insurance = data['insurance']
        if 'incidental' in data: decl.incidental = data['incidental']
        if 'documents' in data: decl.documents = data['documents']
        if 'marks_and_notes' in data: decl.marks_and_notes = data['marks_and_notes']
        if 'container_mode' in data: decl.container_mode = data['container_mode']
        
        # 记录审计日志
        changed_fields = [k for k in data.keys() if k in decl.__dict__]
        if changed_fields:
            audit_service.log_update(
                decl.id,
                old_data={},  # 可以优化为记录实际旧值
                new_data=data,
                changes=changed_fields
            )
        
        db.session.commit()
        return decl

    def import_declaration_from_excel(self, file_path: str, source_data: dict = None, created_by: int = None) -> CustomsDeclaration:
        """
        从 Excel 导入报关/装箱单
        """
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            raise BusinessError(f"Failed to read Excel: {str(e)}", 400)
            
        # Basic Validation
        required_cols = ['SKU', 'Quantity']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise BusinessError(f"Missing columns: {missing}", 400)
            
        items_data = []
        fob_total = 0
        
        # Determine Supplier (Name -> ID)
        supplier_map = {}
        if 'Supplier' in df.columns:
            supplier_names = df['Supplier'].dropna().unique().tolist()
            suppliers = db.session.query(SysSupplier).filter(SysSupplier.name.in_(supplier_names)).all()
            supplier_map = {s.name: s.id for s in suppliers}

        for _, row in df.iterrows():
            sku = str(row['SKU']).strip()
            qty = float(row['Quantity'])
            price = float(row.get('Price(USD)', 0))
            
            # Placeholder resolution (Product ID = 1 if not found)
            product_id = 1 
            
            supplier_name = row.get('Supplier')
            supplier_id = supplier_map.get(supplier_name)
            
            items_data.append({
                'product_id': product_id,
                'supplier_id': supplier_id,
                'sku': sku,
                'qty': qty,
                'unit': row.get('Unit', 'PCS'),
                'usd_unit_price': price,
                'usd_total': qty * price,
                'box_no': str(row.get('BoxNo', '')),
                'net_weight': row.get('NetWeight'),
                'gross_weight': row.get('GrossWeight')
            })
            fob_total += qty * price
            
        if not source_data:
            source_data = {}
            
        decl_data = {
            'export_date': source_data.get('export_date'),
            'bill_of_lading_no': source_data.get('shipping_no'),
            'logistics_provider': source_data.get('logistics_provider'),
            'container_mode': source_data.get('container_mode'),
            'source_type': 'excel_import',
            'source_file_url': file_path,
            'fob_total': fob_total,
            'items': items_data
        }
        
        return self.create_declaration(decl_data, created_by)

    def generate_contracts_from_declaration(self, declaration_id: int) -> List[int]:
        """
        根据报关单自动拆分生成交付合同
        """
        decl = db.session.get(CustomsDeclaration, declaration_id)
        if not decl:
            raise BusinessError("Declaration not found", 404)
            
        if decl.status != CustomsStatus.DRAFT.value:
            raise BusinessError("Only DRAFT declaration can generate contracts", 400)
            
        # 1. Group items by Supplier
        items_by_supplier = {}
        for item in decl.items:
            if not item.supplier_id:
                continue
                
            if item.supplier_id not in items_by_supplier:
                items_by_supplier[item.supplier_id] = []
            items_by_supplier[item.supplier_id].append(item)
            
        generated_contract_ids = []
        
        # 2. Generate Contracts
        for supplier_id, items in items_by_supplier.items():
            supplier = db.session.get(SysSupplier, supplier_id)
            
            contract = ScmDeliveryContract(
                contract_no=f"CON-{decl.bill_of_lading_no or decl.pre_entry_no or decl.id}-{supplier.code or supplier.id}",
                customs_declaration_id=decl.id,
                supplier_id=supplier_id,
                company_id=1,
                event_date=decl.export_date or datetime.date.today(),
                delivery_date=decl.shipping_date,
                status=ContractStatus.PENDING.value,
                currency="CNY",
                notes=f"Generated from Declaration {decl.pre_entry_no or decl.id}"
            )
            db.session.add(contract)
            db.session.flush()
            
            total_amount = 0
            
            for item in items:
                # Mock price: usd * 7
                unit_price_cny = item.usd_unit_price * 7 
                
                contract_item = ScmDeliveryContractItem(
                    l1_contract_id=contract.id,
                    product_id=item.product_id,
                    confirmed_qty=item.qty,
                    unit_price=unit_price_cny,
                    total_price=item.qty * unit_price_cny,
                    notes=f"From SKU: {item.sku}"
                )
                db.session.add(contract_item)
                total_amount += contract_item.total_price
                
            contract.total_amount = total_amount
            generated_contract_ids.append(contract.id)
            
        # 3. Update Declaration Status
        if generated_contract_ids:
            decl.status = 'processing'
            
        db.session.commit()
        return generated_contract_ids

    def get_archive_path(self, declaration_id: int, category: str = None) -> str:
        """
        生成报关单归档路径
        Format: {InternalShipper}/{EntryNo}[/{Category}]
        """
        decl = self.get_declaration(declaration_id)
        if not decl:
            raise BusinessError("Declaration not found", 404)
            
        # 1. 确定经营单位 (文件夹一级)
        # 如果有关联内部经营单位，用名称；否则用 'Unassigned'
        company_name = 'Unassigned'
        if decl.internal_shipper and decl.internal_shipper.legal_name:
            company_name = decl.internal_shipper.legal_name
            
        # 2. 确定报关单号 (文件夹二级)
        # 优先用 pre_entry_no (预录入编号)，其次用 customs_no (海关编号)，再用 filing_no (申报号)
        # 如果还是草稿且没有这些号，用 'Draft_{id}'
        folder_name = decl.pre_entry_no or decl.customs_no or decl.filing_no
        if not folder_name:
            folder_name = f"Draft_{decl.id}"
            
        # 3. Sanitize (简单的非法字符替换)
        def sanitize(s):
            return "".join([c for c in s if c.isalnum() or c in (' ', '-', '_', '.')]).strip()
            
        safe_company = sanitize(company_name)
        safe_folder = sanitize(folder_name)
        
        base_path = f"{safe_company}/{safe_folder}"
        
        if category:
            # 兼容旧逻辑：如果请求明确要子目录
            return f"{base_path}/{category}"
            
        return base_path

    def sync_nas_files(self, declaration_id: int):
        """
        同步 NAS 文件状态到数据库
        """
        try:
            client = SynologyClient()
            rel_path = self.get_archive_path(declaration_id)
            
            # 1. 获取 NAS 上的文件列表 (扁平化)
            # 注意: list_files 需要支持扫描
            nas_files_list = client.list_files(rel_path)
            
            # 将 NAS 文件映射为 {文件名: Info}
            # 过滤掉子文件夹，只关注根目录下的文件(新逻辑)
            # 如果要兼容旧逻辑，还需要递归扫描子目录，这里暂只处理根目录扁平化文件
            nas_files = {f['name']: f for f in nas_files_list if not f['isdir']}
            
            # 2. 获取数据库记录
            db_atts = db.session.query(CustomsAttachment).filter_by(declaration_id=declaration_id).all()
            db_files_map = {att.file_path: att for att in db_atts}
            
            # 3. 比对: 检查数据库记录是否在 NAS 上丢失
            for path, att in db_files_map.items():
                # path 可能是 '报关单.pdf' (新) 或 '01_Customs/报关单.pdf' (旧)
                # 简单起见，我们只检查文件名匹配
                # 如果是旧路径包含 /, 暂时跳过或尝试匹配
                if '/' in path:
                    continue 
                    
                if path not in nas_files:
                    if att.status != 'missing':
                        att.status = 'missing'
                        att.sync_message = f"Detected missing at {dt.now()}"
                        db.session.add(att)
                else:
                    # 恢复正常
                    if att.status == 'missing':
                        att.status = 'synced'
                        att.sync_message = None
                        db.session.add(att)
                        
            # 4. 比对: 检查 NAS 上的新文件 (自动发现)
            for name, info in nas_files.items():
                if name not in db_files_map:
                    # 自动入库
                    new_att = CustomsAttachment(
                        declaration_id=declaration_id,
                        file_name=name,
                        file_path=name,
                        file_size=info['size'],
                        file_type=name.split('.')[-1].lower() if '.' in name else '',
                        category='04_Others', # 默认为其他
                        source='nas_sync',
                        status='synced',
                        sync_message='Auto discovered from NAS'
                    )
                    db.session.add(new_att)
            
            db.session.commit()
            
        except Exception as e:
            # 同步失败不应阻断主流程，记录日志即可
            print(f"Sync failed for declaration {declaration_id}: {e}")
            pass

    def split_pdf(self, file_storage, declaration_id: int):
        """
        尝试拆分 PDF 文件
        返回拆分后的文件列表: [{'filename': '...', 'stream': BytesIO, 'slot_title': '...'}]
        """
        try:
            from pypdf import PdfReader, PdfWriter
            import io
            
            # 确保指针在开始位置
            file_storage.seek(0)
            try:
                reader = PdfReader(file_storage)
            except Exception:
                # 并不是有效的PDF
                file_storage.seek(0)
                return None
            
            splitted_files = {} # {'报关单': writer, ...}
            
            # 关键词映射
            keywords_map = {
                '中华人民共和国海关出口货物报关单': '报关单',
                '通关无纸化出口放行通知书': '放行通知书',
                '委托报关协议': '委托报关协议'
            }
            
            has_split = False
            
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if not text:
                    continue
                    
                target_slot = None
                for keyword, slot in keywords_map.items():
                    if keyword in text:
                        target_slot = slot
                        break
                
                if target_slot:
                    has_split = True
                    if target_slot not in splitted_files:
                        splitted_files[target_slot] = PdfWriter()
                    splitted_files[target_slot].add_page(page)
            
            # 复位指针，以免影响后续使用
            file_storage.seek(0)

            if not has_split:
                return None
                
            results = []
            decl = self.get_declaration(declaration_id)
            ref_no = decl.pre_entry_no or decl.customs_no or str(decl.id)
            ref_no = "".join([c for c in ref_no if c.isalnum() or c in '-_'])
            
            for slot, writer in splitted_files.items():
                out_stream = io.BytesIO()
                writer.write(out_stream)
                out_stream.seek(0)
                
                # 生成文件名
                # 统一格式: {插槽名}_{单号}.pdf
                filename = f"{slot}_{ref_no}.pdf"
                
                results.append({
                    'filename': filename,
                    'stream': out_stream,
                    'slot_title': slot,
                    'file_size': out_stream.getbuffer().nbytes
                })
                
            return results
            
        except ImportError:
            print("pypdf not installed")
            return None
        except Exception as e:
            print(f"PDF split failed: {e}")
            file_storage.seek(0)
            return None

    def image_to_pdf(self, file_storage, declaration_id: int):
        """
        将图片转换为 PDF (A4 规格, 居中适配, 智能压缩)
        返回: {'filename': ..., 'stream': BytesIO, 'file_size': int}
        """
        try:
            from PIL import Image, ImageOps
            import io
            
            # A4 尺寸 (150 DPI)
            A4_WIDTH, A4_HEIGHT = 1240, 1754 
            MARGIN = 50 

            # 确保指针
            file_storage.seek(0)
            
            try:
                # 1. 尝试打开图片
                img = Image.open(file_storage)
                
                # 2. 处理 EXIF 旋转 (手机照片常见问题)
                img = ImageOps.exif_transpose(img)
                
                # 3. 颜色模式转换
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 4. 计算缩放比例
                img_w, img_h = img.size
                target_w = A4_WIDTH - 2 * MARGIN
                target_h = A4_HEIGHT - 2 * MARGIN
                
                ratio = min(target_w / img_w, target_h / img_h)
                
                # 策略: 如果图片比 A4 打印区域小，保持原样(ratio=1)；如果大，缩小适配
                if ratio > 1:
                    ratio = 1
                    
                new_w = int(img_w * ratio)
                new_h = int(img_h * ratio)
                
                # 5. 重采样 (高质量缩小)
                if ratio != 1:
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # 6. 创建 A4 画布
                canvas = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), (255, 255, 255))
                
                # 7. 居中粘贴
                x = (A4_WIDTH - new_w) // 2
                y = (A4_HEIGHT - new_h) // 2
                canvas.paste(img, (x, y))
                
                # 8. 保存为 PDF
                out_stream = io.BytesIO()
                # quality=85 对 JPEG 压缩非常有效
                canvas.save(out_stream, "PDF", resolution=150.0, quality=85)
                out_stream.seek(0)
                
                # 生成文件名: 替换扩展名为 pdf
                original_name = file_storage.filename
                if '.' in original_name:
                    name_part = original_name.rsplit('.', 1)[0]
                else:
                    name_part = original_name
                
                target_filename = f"{name_part}.pdf"
                
                # 复位原始指针
                file_storage.seek(0)
                
                return {
                    'filename': target_filename,
                    'stream': out_stream,
                    'file_size': out_stream.getbuffer().nbytes
                }
                
            except Exception as e:
                # 不是有效图片或转换失败
                print(f"Image conversion failed: {e}")
                file_storage.seek(0)
                return None
                
        except ImportError:
            print("Pillow not installed")
            return None

customs_service = CustomsService()

