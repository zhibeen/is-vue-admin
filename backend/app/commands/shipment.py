"""发货单管理命令"""
import click
from flask.cli import with_appcontext
from decimal import Decimal
from datetime import datetime, timedelta
import random
from sqlalchemy import func

from app.extensions import db
from app.models.logistics.shipment import ShipmentOrder, ShipmentOrderItem, ShipmentStatus, ShipmentSource
from app.models.logistics.purchase_item import ShipmentPurchaseItem
from app.models.serc.foundation import SysCompany
from app.models.purchase.supplier import SysSupplier
from app.models.product import Product, ProductVariant


@click.group()
def shipment():
    """发货单管理命令"""
    pass


@shipment.command('seed-mock')
@click.option('--count', '-c', default=20, help='生成发货单数量')
@click.option('--clear', is_flag=True, help='清除现有模拟数据')
@with_appcontext
def seed_mock_shipments(count, clear):
    """生成模拟发货单数据
    
    示例:
        flask shipment seed-mock              # 生成20条
        flask shipment seed-mock -c 50        # 生成50条
        flask shipment seed-mock --clear -c 10  # 清除后生成10条
    """
    
    # 清除现有模拟数据
    if clear:
        click.echo('🗑️  清除现有模拟数据...')
        mock_shipments = ShipmentOrder.query.filter(
            ShipmentOrder.notes.like('%模拟发货单%')
        ).all()
        for s in mock_shipments:
            db.session.delete(s)
        db.session.commit()
        click.echo(f'  ✅ 已清除 {len(mock_shipments)} 条模拟数据')
    
    # 获取第一个公司作为发货公司
    company = SysCompany.query.first()
    if not company:
        click.echo('❌ 未找到发货公司，请先创建公司数据')
        click.echo('   运行: docker compose exec backend flask company seed')
        return
    
    # 获取所有供应商
    suppliers = SysSupplier.query.limit(5).all()
    if not suppliers:
        click.echo('❌ 未找到供应商，请先创建供应商数据')
        click.echo('   运行: docker compose exec backend flask supplier seed')
        return
    
    # 获取一些产品变体（SKU）
    product_variants = ProductVariant.query.filter_by(is_active=True).limit(50).all()
    if not product_variants:
        click.echo('❌ 未找到产品SKU，请先创建产品数据')
        click.echo('   运行: docker compose exec backend flask product seed')
        return
    
    click.echo(f'📦 开始生成 {count} 个模拟发货单...')
    click.echo(f'  - 发货公司: {company.legal_name}')
    click.echo(f'  - 供应商数量: {len(suppliers)}')
    click.echo(f'  - 产品SKU数量: {len(product_variants)}')
    click.echo('')
    
    # 模拟收货国家和客户
    countries_data = {
        'US': ['Amazon US Warehouse', 'Walmart Distribution', 'Target Logistics', 'Best Buy Center'],
        'DE': ['Amazon DE Lager', 'MediaMarkt Zentrale', 'Saturn Logistik', 'Otto Versand'],
        'JP': ['Amazon JP 倉庫', 'Rakuten物流', 'ヨドバシカメラ', 'ビックカメラ'],
        'GB': ['Amazon UK Warehouse', 'Tesco Distribution', 'Argos Logistics', 'John Lewis'],
        'AU': ['Amazon AU Warehouse', 'Coles Distribution', 'Woolworths Logistics', 'JB Hi-Fi'],
        'FR': ['Amazon FR Entrepôt', 'Carrefour Logistique', 'Fnac Darty', 'Leclerc'],
        'CA': ['Amazon CA Warehouse', 'Best Buy Canada', 'Canadian Tire', 'Loblaws'],
    }
    
    # 物流商和运输方式
    logistics_configs = [
        {'provider': 'DHL Express', 'method': '空运', 'days': (3, 7)},
        {'provider': 'FedEx International', 'method': '空运', 'days': (5, 10)},
        {'provider': 'UPS Worldwide', 'method': '空运', 'days': (4, 8)},
        {'provider': 'EMS', 'method': '空运', 'days': (7, 14)},
        {'provider': 'Maersk Line', 'method': '海运', 'days': (25, 35)},
        {'provider': 'COSCO Shipping', 'method': '海运', 'days': (28, 40)},
        {'provider': 'SF Express', 'method': '快递', 'days': (2, 5)},
        {'provider': 'YTO Express', 'method': '快递', 'days': (3, 7)},
    ]
    
    # 不同来源的分布
    sources = [
        (ShipmentSource.MANUAL.value, 40),      # 40% 手工
        (ShipmentSource.EXCEL.value, 20),       # 20% Excel
        (ShipmentSource.LINGXING.value, 30),    # 30% 领星
        (ShipmentSource.YICANG.value, 10),      # 10% 易仓
    ]
    
    # 不同状态的分布
    statuses = [
        (ShipmentStatus.DRAFT.value, 30),       # 30% 草稿
        (ShipmentStatus.CONFIRMED.value, 40),   # 40% 已确认
        (ShipmentStatus.SHIPPED.value, 25),     # 25% 已发货
        (ShipmentStatus.COMPLETED.value, 5),    # 5% 已完成
    ]
    
    created_count = 0
    skipped_count = 0
    
    for i in range(count):
        today = datetime.now()
        # 生成过去90天内的随机日期
        ship_date = today - timedelta(days=random.randint(0, 90))
        
        # 生成发货单号
        date_str = ship_date.strftime('%Y%m%d')
        shipment_no = f"SH-{date_str}-{random.randint(1000, 9999)}"
        
        # 检查是否已存在
        existing = ShipmentOrder.query.filter_by(shipment_no=shipment_no).first()
        if existing:
            skipped_count += 1
            continue
        
        # 随机选择国家和客户
        country = random.choice(list(countries_data.keys()))
        consignee_name = random.choice(countries_data[country])
        
        # 随机选择物流配置
        logistics = random.choice(logistics_configs)
        
        # 加权随机选择来源和状态
        source = random.choices(
            [s[0] for s in sources],
            weights=[s[1] for s in sources]
        )[0]
        
        status = random.choices(
            [s[0] for s in statuses],
            weights=[s[1] for s in statuses]
        )[0]
        
        # 如果是已发货或已完成，设置实际发货日期
        actual_ship_date = None
        if status in [ShipmentStatus.SHIPPED.value, ShipmentStatus.COMPLETED.value]:
            actual_ship_date = (ship_date + timedelta(days=random.randint(1, 3))).date()
        
        # 生成外部订单号（如果来自外部系统）
        external_order_no = None
        external_tracking_no = None
        if source == ShipmentSource.LINGXING.value:
            external_order_no = f'LX-{random.randint(10000000, 99999999)}'
            external_tracking_no = f'FBA{random.choice(["15", "16", "17"])}{random.randint(10000000, 99999999)}'
        elif source == ShipmentSource.YICANG.value:
            external_order_no = f'YC-{random.randint(10000000, 99999999)}'
            external_tracking_no = f'OW{random.randint(100000000, 999999999)}'
        
        # === 新增：仓库信息 ===
        # 随机决定是FBA还是第三方仓
        destination_warehouse_type = random.choice(['fba', 'third_party'])
        is_fba = destination_warehouse_type == 'fba'
        
        # 发货仓库信息
        origin_warehouse_types = ['self', 'factory', 'supplier']
        origin_warehouse_type = random.choice(origin_warehouse_types)
        is_factory_direct = 1 if origin_warehouse_type == 'factory' else 0
        
        origin_warehouse_names = {
            'self': ['深圳自营仓', '广州中心仓', '东莞配送中心', '佛山物流仓'],
            'factory': ['广州工厂仓', '东莞生产基地仓', '惠州制造中心', '中山生产车间'],
            'supplier': ['供应商A仓库', '供应商B发货中心', '供应商C物流仓', '协作商仓储中心']
        }
        origin_warehouse_name = random.choice(origin_warehouse_names[origin_warehouse_type])
        origin_warehouse_address = f'广东省{random.choice(["深圳市", "广州市", "东莞市", "佛山市"])}{random.choice(["龙岗区", "宝安区", "南山区", "天河区", "黄埔区"])}工业园{random.randint(1, 50)}号'
        
        # 收货仓库信息
        fba_shipment_id = None
        fba_center_codes = None
        marketplace = None
        warehouse_service_provider = None
        warehouse_contact = None
        warehouse_contact_phone = None
        
        if is_fba:
            # FBA相关信息
            fba_shipment_id = f'FBA{random.randint(10000000, 99999999)}'
            fba_centers = {
                'US': ['PHX7', 'LGB6', 'ONT8', 'SMF7', 'DFW7'],
                'DE': ['FRA1', 'BER3', 'LEJ1', 'MUC3'],
                'JP': ['NRT1', 'KIX2', 'HND9'],
                'GB': ['LHR2', 'MAN3', 'BHX4'],
            }
            destination_warehouse_code = random.choice(fba_centers.get(country, ['XXX1']))
            fba_center_codes = [destination_warehouse_code]
            if random.random() > 0.7:  # 30%的概率分配到多个FBA中心
                additional_center = random.choice(fba_centers.get(country, ['XXX2']))
                if additional_center != destination_warehouse_code:
                    fba_center_codes.append(additional_center)
            
            marketplace = country
            destination_warehouse_name = f'Amazon {country} {destination_warehouse_code}'
            destination_warehouse_address = f'{destination_warehouse_code} Amazon Fulfillment Center, {country}'
        else:
            # 第三方仓信息
            third_party_warehouses = [
                {'provider': 'FlexPort Logistics', 'contact': 'John Smith', 'phone': '+1-555-0123'},
                {'provider': 'Shipbob Warehouse', 'contact': 'Emily Chen', 'phone': '+1-555-0456'},
                {'provider': 'Rakuten Super Logistics', 'contact': 'Yuki Tanaka', 'phone': '+81-3-1234-5678'},
                {'provider': 'Red Stag Fulfillment', 'contact': 'Mike Johnson', 'phone': '+1-865-123-4567'},
                {'provider': 'Fulfillment by Wingo', 'contact': 'Sarah Williams', 'phone': '+1-617-555-0789'},
            ]
            warehouse_info = random.choice(third_party_warehouses)
            warehouse_service_provider = warehouse_info['provider']
            warehouse_contact = warehouse_info['contact']
            warehouse_contact_phone = warehouse_info['phone']
            
            destination_warehouse_code = f'WH{random.randint(100, 999)}'
            destination_warehouse_name = f'{warehouse_service_provider} - {destination_warehouse_code}'
            destination_warehouse_address = f'{random.randint(1000, 9999)} Warehouse Blvd, {country}'
        
        # === 新增：物流扩展信息 ===
        logistics_service_types = ['标准运输', '加急运输', '经济运输', '特快专递']
        logistics_service_type = random.choice(logistics_service_types)
        
        freight_terms = ['prepaid', 'collect', 'third_party']
        freight_term = random.choice(freight_terms)
        
        packing_methods = ['纸箱', '木箱', '托盘', '散装']
        packing_method = random.choice(packing_methods)
        
        # === 新增：时间节点扩展 ===
        transit_days_min, transit_days_max = logistics['days']
        estimated_arrival_date = (ship_date + timedelta(days=random.randint(transit_days_min, transit_days_max))).date()
        
        actual_arrival_date = None
        warehouse_received_date = None
        completed_date = None
        
        if status == ShipmentStatus.COMPLETED.value:
            actual_days = random.randint(transit_days_min, transit_days_max + 3)
            actual_arrival_date = (ship_date + timedelta(days=actual_days)).date()
            warehouse_received_date = datetime.combine(actual_arrival_date, datetime.min.time()) + timedelta(hours=random.randint(1, 12))
            completed_date = warehouse_received_date + timedelta(days=random.randint(1, 3))
        elif status == ShipmentStatus.SHIPPED.value and random.random() > 0.5:
            # 50%的已发货订单已到达
            actual_days = random.randint(transit_days_min, transit_days_max + 3)
            actual_arrival_date = (ship_date + timedelta(days=actual_days)).date()
            if random.random() > 0.5:
                warehouse_received_date = datetime.combine(actual_arrival_date, datetime.min.time()) + timedelta(hours=random.randint(1, 12))
        
        # === 新增：财务信息（先初始化，后续计算） ===
        # VAT税号（仅欧洲国家）
        vat_number = None
        if country in ['DE', 'GB', 'FR']:
            vat_number = f'{country}{random.randint(100000000, 999999999)}'
        
        # 创建发货单
        shipment = ShipmentOrder(
            shipment_no=shipment_no,
            source=source,
            status=status,
            shipper_company_id=company.id,
            consignee_name=consignee_name,
            consignee_address=f'{random.randint(100, 9999)} {random.choice(["Main St", "Oak Ave", "Industrial Blvd", "Commerce Dr"])}, {random.choice(["Suite", "Building", "Unit"])} {random.randint(1, 99)}',
            consignee_country=country,
            
            # 仓库信息
            origin_warehouse_name=origin_warehouse_name,
            origin_warehouse_type=origin_warehouse_type,
            origin_warehouse_address=origin_warehouse_address,
            is_factory_direct=is_factory_direct,
            destination_warehouse_name=destination_warehouse_name,
            destination_warehouse_code=destination_warehouse_code,
            destination_warehouse_type=destination_warehouse_type,
            destination_warehouse_address=destination_warehouse_address,
            
            # FBA专用
            fba_shipment_id=fba_shipment_id,
            fba_center_codes=fba_center_codes,
            marketplace=marketplace,
            
            # 第三方仓专用
            warehouse_service_provider=warehouse_service_provider,
            warehouse_contact=warehouse_contact,
            warehouse_contact_phone=warehouse_contact_phone,
            
            # 物流信息
            logistics_provider=logistics['provider'],
            logistics_service_type=logistics_service_type,
            tracking_no=f'{logistics["provider"][:3].upper()}{random.randint(100000000, 999999999)}',
            shipping_method=logistics['method'],
            freight_term=freight_term,
            
            # 时间节点
            estimated_ship_date=ship_date.date(),
            actual_ship_date=actual_ship_date,
            estimated_arrival_date=estimated_arrival_date,
            actual_arrival_date=actual_arrival_date,
            warehouse_received_date=warehouse_received_date,
            completed_date=completed_date,
            
            # 包装信息
            total_packages=random.randint(1, 20),
            packing_method=packing_method,
            total_gross_weight=None,  # 后续计算
            total_net_weight=None,    # 后续计算
            volumetric_weight=None,   # 后续计算
            chargeable_weight=None,   # 后续计算
            
            # 财务信息（部分后续计算）
            currency='CNY',
            vat_number=vat_number,
            cost_allocation_method=random.choice(['volume', 'weight', 'quantity', 'value']),
            
            # 外部系统
            external_order_no=external_order_no,
            external_tracking_no=external_tracking_no,
            
            # 关联状态
            is_declared=status in [ShipmentStatus.COMPLETED.value] or random.random() < 0.2,
            is_contracted=status in [ShipmentStatus.CONFIRMED.value, ShipmentStatus.SHIPPED.value, ShipmentStatus.COMPLETED.value] and random.random() < 0.7,
            
            notes=f'模拟发货单 #{i+1} - {source} - {destination_warehouse_type.upper()}'
        )
        
        db.session.add(shipment)
        db.session.flush()
        
        # 为每个发货单添加明细
        item_count = random.randint(3, 8)
        total_amount = Decimal('0')
        total_tax_amount = Decimal('0')
        total_amount_with_tax = Decimal('0')
        total_gross = Decimal('0')
        total_net = Decimal('0')
        
        # 随机选择1-3个供应商（模拟混合供货）
        selected_suppliers = random.sample(suppliers, min(random.randint(1, 3), len(suppliers)))
        
        for j in range(item_count):
            # 随机选择产品变体（SKU）和供应商
            variant = random.choice(product_variants)
            supplier = random.choice(selected_suppliers)
            
            # 随机生成数量和价格
            quantity = Decimal(str(random.randint(50, 500)))
            # 如果产品有价格，使用产品价格，否则随机生成
            if variant.price:
                unit_price = variant.price
            else:
                unit_price = Decimal(str(random.uniform(5, 200))).quantize(Decimal('0.01'))
            
            tax_rate = Decimal('0.13')  # 13%税率
            
            # 计算金额
            total_price = quantity * unit_price
            unit_price_with_tax = unit_price * (1 + tax_rate)
            tax_amount = total_price * tax_rate
            total_price_with_tax = total_price + tax_amount
            
            # 计算重量
            unit_weight = Decimal(str(random.uniform(0.05, 3))).quantize(Decimal('0.01'))
            total_weight = unit_weight * quantity
            gross_weight = total_weight * Decimal('1.1')  # 毛重约为净重的1.1倍
            
            # 累加
            total_amount += total_price
            total_tax_amount += tax_amount
            total_amount_with_tax += total_price_with_tax
            total_net += total_weight
            total_gross += gross_weight
            
            # 生成HS CODE和出口申报名称
            hs_code = f'{random.randint(8700, 8800)}.{random.randint(10, 99)}.{random.randint(10, 99)}'
            export_names = [
                '汽车零部件',
                '汽车配件及附件',
                '车用塑料制品',
                '车用橡胶制品',
                '车用金属制品',
                '车用电子元件',
                '汽车装饰用品',
                '车载电子设备'
            ]
            export_name = random.choice(export_names)
            
            # 海关申报单位
            customs_units = ['千克', '个', '套', '件', '台', '只']
            customs_unit = random.choice(customs_units)
            
            # === 新增：FBA和第三方仓字段 ===
            fnsku = None
            msku = None
            asin = None
            marketplace_listing_id = None
            warehouse_matched_qty = None
            warehouse_received_qty = None
            warehouse_pending_qty = None
            shelf_location = None
            package_no = None
            barcode = None
            unit_volume = None
            
            if is_fba:
                # FBA字段
                fnsku = f'X00{random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}{random.randint(100000, 999999)}'
                msku = f'{variant.sku}-{random.choice(["US", "UK", "DE", "JP"])}'
                asin = f'B0{random.randint(10000000, 99999999):08d}'
                marketplace_listing_id = f'{asin}-{random.randint(1, 99)}'
            else:
                # 第三方仓字段
                warehouse_matched_qty = float(quantity)
                if status == ShipmentStatus.COMPLETED.value:
                    warehouse_received_qty = float(quantity)
                    warehouse_pending_qty = 0
                elif status == ShipmentStatus.SHIPPED.value:
                    received = float(quantity) * random.uniform(0, 0.8)
                    warehouse_received_qty = received
                    warehouse_pending_qty = float(quantity) - received
                else:
                    warehouse_received_qty = 0
                    warehouse_pending_qty = float(quantity)
                
                shelf_location = f'{random.choice(["A", "B", "C", "D"])}-{random.randint(1, 50):02d}-{random.randint(1, 10):02d}'
            
            # 包装信息
            package_no = f'PKG-{i+1}-{j+1}'
            barcode = f'{random.randint(1000000000000, 9999999999999)}'
            unit_volume = float(Decimal(str(random.uniform(0.001, 0.1))).quantize(Decimal('0.001')))
            
            # 创建明细
            item = ShipmentOrderItem(
                shipment_id=shipment.id,
                product_id=variant.product_id,
                sku=variant.sku,
                product_name=variant.product.name if variant.product else f'Product {variant.sku}',
                product_name_en=f'{variant.product.name} (EN)' if variant.product else f'Product {variant.sku} (EN)',
                quantity=quantity,
                unit='PCS',
                hs_code=hs_code,
                export_name=export_name,
                customs_unit=customs_unit,
                unit_price=unit_price,
                total_price=total_price,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                unit_price_with_tax=unit_price_with_tax,
                total_price_with_tax=total_price_with_tax,
                supplier_id=supplier.id,
                unit_weight=unit_weight,
                total_weight=total_weight,
                unit_volume=unit_volume,
                origin_country='CN',
                
                # FBA字段
                fnsku=fnsku,
                msku=msku,
                asin=asin,
                marketplace_listing_id=marketplace_listing_id,
                
                # 第三方仓字段
                warehouse_matched_qty=warehouse_matched_qty,
                warehouse_received_qty=warehouse_received_qty,
                warehouse_pending_qty=warehouse_pending_qty,
                shelf_location=shelf_location,
                
                # 包装信息
                package_no=package_no,
                barcode=barcode,
            )
            
            db.session.add(item)
        
        # 刷新session以获取item的ID
        db.session.flush()
        
        # 为每个商品明细生成1-3个采购明细
        for item in shipment.items:
            # 随机生成1-3个采购明细（模拟从不同采购单/批次汇总而成）
            purchase_item_count = random.randint(1, 3)
            remaining_qty = int(item.quantity)
            
            for pi in range(purchase_item_count):
                if remaining_qty <= 0:
                    break
                
                # 随机分配数量
                if pi == purchase_item_count - 1:
                    # 最后一个采购明细包含剩余全部数量
                    pi_quantity = remaining_qty
                else:
                    # 随机分配20%-60%的剩余数量
                    pi_quantity = int(remaining_qty * random.uniform(0.2, 0.6))
                    if pi_quantity == 0:
                        pi_quantity = remaining_qty
                
                remaining_qty -= pi_quantity
                
                # 随机选择一个供应商（可能与商品明细的供应商不同）
                pi_supplier = random.choice(suppliers)
                
                # 生成采购单号
                po_date = (ship_date - timedelta(days=random.randint(30, 120))).strftime('%Y%m%d')
                po_no = f"PO-{po_date}-{random.randint(1000, 9999)}"
                
                # 采购价格（比商品明细的单价低5%-20%，模拟成本价）
                if item.unit_price:
                    discount = random.uniform(0.80, 0.95)
                    pu_unit_price = float(item.unit_price) * discount
                else:
                    pu_unit_price = random.uniform(10, 500)
                
                pu_total_price = pu_unit_price * pi_quantity
                
                # 生成批次号
                batch_no = f"BATCH-{po_date}-{random.randint(100, 999)}"
                
                # 生产日期和有效期
                production_date = (ship_date - timedelta(days=random.randint(60, 180))).date()
                expire_date = None
                if random.random() > 0.7:  # 30%的商品有有效期
                    expire_days = random.randint(365, 1095)  # 1-3年有效期
                    expire_date = (production_date + timedelta(days=expire_days))
                
                purchase_item = ShipmentPurchaseItem(
                    shipment_order_id=shipment.id,
                    purchase_order_no=po_no,
                    purchase_line_id=random.randint(1, 10),
                    product_variant_id=variant.id,
                    sku=item.sku,
                    product_name=item.product_name,
                    quantity=pi_quantity,
                    unit=item.unit or '件',
                    purchase_unit_price=pu_unit_price,
                    purchase_total_price=pu_total_price,
                    purchase_currency='CNY',
                    supplier_id=pi_supplier.id,
                    supplier_name=pi_supplier.name,
                    batch_no=batch_no,
                    production_date=production_date,
                    expire_date=expire_date,
                    notes=f'模拟采购明细 - 来自采购单 {po_no}'
                )
                
                db.session.add(purchase_item)
        
        # 更新发货单汇总信息
        shipment.total_amount = total_amount
        shipment.total_tax_amount = total_tax_amount
        shipment.total_amount_with_tax = total_amount_with_tax
        shipment.total_net_weight = total_net
        shipment.total_gross_weight = total_gross
        total_volume_calc = (total_gross / Decimal('200')).quantize(Decimal('0.001'))
        shipment.total_volume = total_volume_calc
        
        # === 新增：计算财务信息 ===
        # 体积重和计费重
        volumetric_weight = total_volume_calc * Decimal('200')  # 1m³ = 200kg
        shipment.volumetric_weight = volumetric_weight
        # 计费重取实重和体积重的较大值
        shipment.chargeable_weight = max(total_gross, volumetric_weight)
        
        # 货物价值（商品明细的不含税总金额）
        shipment.total_goods_value = total_amount
        
        # 申报价值（通常为货物价值的80%-95%）
        declared_value_ratio = Decimal(str(random.uniform(0.80, 0.95)))
        shipment.declared_value = (total_amount * declared_value_ratio).quantize(Decimal('0.01'))
        
        # 物流成本
        # 运费：根据运输方式和重量计算
        if logistics['method'] == '海运':
            freight_per_kg = Decimal(str(random.uniform(2, 5)))
        elif logistics['method'] == '空运':
            freight_per_kg = Decimal(str(random.uniform(15, 30)))
        else:  # 快递
            freight_per_kg = Decimal(str(random.uniform(25, 50)))
        
        freight_cost = (shipment.chargeable_weight * freight_per_kg).quantize(Decimal('0.01'))
        shipment.freight_cost = freight_cost
        
        # 保险费（货值的0.3%-0.5%）
        insurance_rate = Decimal(str(random.uniform(0.003, 0.005)))
        shipment.insurance_cost = (total_amount * insurance_rate).quantize(Decimal('0.01'))
        
        # 操作费
        shipment.handling_fee = Decimal(str(random.uniform(50, 200))).quantize(Decimal('0.01'))
        
        # 其他费用
        shipment.other_costs = Decimal(str(random.uniform(0, 100))).quantize(Decimal('0.01'))
        
        # 物流总成本
        shipment.total_logistics_cost = (
            freight_cost + 
            shipment.insurance_cost + 
            shipment.handling_fee + 
            shipment.other_costs
        ).quantize(Decimal('0.01'))
        
        # 税务信息
        # 欧洲国家有VAT
        if country in ['DE', 'GB', 'FR']:
            tax_rate_percent = Decimal('0.19') if country == 'DE' else Decimal('0.20')  # 德国19%，英国20%
            shipment.tax_rate = tax_rate_percent
            shipment.estimated_tax = (shipment.declared_value * tax_rate_percent).quantize(Decimal('0.01'))
            
            if status == ShipmentStatus.COMPLETED.value:
                # 已完成的订单，实际税费为预估税费的95%-105%
                actual_tax_ratio = Decimal(str(random.uniform(0.95, 1.05)))
                shipment.actual_tax = (shipment.estimated_tax * actual_tax_ratio).quantize(Decimal('0.01'))
            else:
                shipment.actual_tax = None
        
        # 成本核算（从采购明细计算）
        total_purchase_cost = sum(
            Decimal(str(pi.purchase_total_price)) 
            for pi in shipment.purchase_items
        )
        shipment.total_purchase_cost = total_purchase_cost
        
        # 利润率计算（简化：不含税销售额 - 采购成本 - 物流成本）/ 采购成本
        if total_purchase_cost > 0:
            profit = total_amount - total_purchase_cost - shipment.total_logistics_cost
            profit_margin = (profit / total_purchase_cost * 100).quantize(Decimal('0.01'))
            shipment.profit_margin = float(profit_margin)
        
        created_count += 1
        
        # 每10条显示一次进度
        if (i + 1) % 10 == 0 or (i + 1) == count:
            status_icon = {
                ShipmentStatus.DRAFT.value: '📝',
                ShipmentStatus.CONFIRMED.value: '✅',
                ShipmentStatus.SHIPPED.value: '🚢',
                ShipmentStatus.COMPLETED.value: '✔️'
            }.get(status, '📦')
            
            click.echo(f'  {status_icon} [{i+1}/{count}] {shipment_no} | {consignee_name[:20]:20} | {item_count}项 | ¥{float(total_amount_with_tax):,.2f}')
    
    db.session.commit()
    
    click.echo(f'\n✅ 模拟数据生成完成！')
    click.echo(f'  - 成功创建: {created_count} 个发货单')
    if skipped_count > 0:
        click.echo(f'  - 跳过重复: {skipped_count} 个')
    
    # 统计各状态数量
    status_stats = db.session.query(
        ShipmentOrder.status,
        func.count(ShipmentOrder.id)
    ).filter(
        ShipmentOrder.notes.like('%模拟发货单%')
    ).group_by(ShipmentOrder.status).all()
    
    click.echo(f'\n📊 状态分布:')
    status_names = {
        ShipmentStatus.DRAFT.value: '草稿',
        ShipmentStatus.CONFIRMED.value: '已确认',
        ShipmentStatus.SHIPPED.value: '已发货',
        ShipmentStatus.COMPLETED.value: '已完成',
    }
    for status, count in status_stats:
        click.echo(f'  - {status_names.get(status, status)}: {count} 个')
    
    click.echo(f'\n💡 提示:')
    click.echo(f'  - 查看发货单列表: GET http://localhost:5555/api/v1/logistics/shipments')
    click.echo(f'  - 前端访问: http://localhost:5173/#/logistics/shipment')
    click.echo(f'  - 清除数据: docker compose exec backend flask shipment seed-mock --clear')


@shipment.command('init-permissions')
@with_appcontext
def init_permissions():
    """初始化发货单相关权限"""
    from app.models.user import Permission
    
    permissions = [
        {
            'name': 'logistics:shipment:view',
            'module': '物流管理',
            'description': '允许查看发货单列表和详情',
            'resource': '发货单',
            'action': 'view'
        },
        {
            'name': 'logistics:shipment:create',
            'module': '物流管理',
            'description': '允许创建新的发货单',
            'resource': '发货单',
            'action': 'create'
        },
        {
            'name': 'logistics:shipment:update',
            'module': '物流管理',
            'description': '允许修改发货单信息',
            'resource': '发货单',
            'action': 'update'
        },
        {
            'name': 'logistics:shipment:delete',
            'module': '物流管理',
            'description': '允许删除发货单',
            'resource': '发货单',
            'action': 'delete'
        },
        {
            'name': 'logistics:shipment:confirm',
            'module': '物流管理',
            'description': '允许确认发货单',
            'resource': '发货单',
            'action': 'confirm'
        },
        {
            'name': 'logistics:shipment:generate_contracts',
            'module': '物流管理',
            'description': '允许从发货单生成交付合同',
            'resource': '发货单',
            'action': 'generate_contracts'
        },
    ]
    
    created_count = 0
    updated_count = 0
    
    for perm_data in permissions:
        existing = Permission.query.filter_by(name=perm_data['name']).first()
        
        if existing:
            # 更新现有权限
            existing.module = perm_data['module']
            existing.description = perm_data['description']
            existing.resource = perm_data['resource']
            existing.action = perm_data['action']
            updated_count += 1
            click.echo(f"更新权限: {perm_data['name']}")
        else:
            # 创建新权限
            new_permission = Permission(**perm_data)
            db.session.add(new_permission)
            created_count += 1
            click.echo(f"创建权限: {perm_data['name']}")
    
    db.session.commit()
    
    click.echo(f"\n权限初始化完成!")
    click.echo(f"- 新增: {created_count} 个")
    click.echo(f"- 更新: {updated_count} 个")
    click.echo(f"- 总计: {len(permissions)} 个")
    click.echo("\n提示: 请在后台为相应角色分配这些权限")

