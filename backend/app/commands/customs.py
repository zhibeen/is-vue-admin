import click
import random
from faker import Faker
from flask.cli import AppGroup
from app.extensions import db
from datetime import datetime, timedelta, date
from decimal import Decimal

customs_cli = AppGroup('customs')

@click.command('seed-declarations')
@click.option('--count', default=10, help='生成报关单数量')
@click.option('--clear', is_flag=True, help='清除现有报关单数据')
def seed_declarations_cmd(count, clear):
    """生成虚拟报关单 (CustomsDeclaration)"""
    from app.models.customs import CustomsDeclaration, CustomsDeclarationItem, CustomsProduct
    from app.models.product import Product
    from app.models.purchase.supplier import SysSupplier
    from app.models.serc.foundation import SysCompany
    from app.models.serc.enums import CustomsStatus
    
    # 模拟数据常量
    PORTS = ['北仑海关', '洋山海关', '蛇口海关', '盐田海关']
    TRANSPORT_MODES = ['水路运输', '航空运输', '铁路运输']
    TRADE_MODES = ['0110', '9810', '9710']
    EXEMPTION_NATURES = ['101', '502', '503']
    COUNTRIES = ['美国', '德国', '日本', '英国', '澳大利亚']
    PACKAGES = ['4M', '2M', '7M'] # 纸箱, 托盘, 木箱 (使用海关代码)
    CONTAINER_MODES = ['FCL', 'LCL']  # 整柜/散货
    CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY']
    
    if clear:
        click.echo("正在清除现有报关单数据...")
        from app.models.customs.attachment import CustomsAttachment
        from app.models.customs.audit_log import CustomsDeclarationAuditLog
        from app.models.product.item import ProductVariant
        
        # 1. 清除报关单相关（注意外键依赖顺序）
        db.session.query(CustomsAttachment).delete()
        db.session.query(CustomsDeclarationAuditLog).delete()  # 先删除审计日志
        db.session.query(CustomsDeclarationItem).delete()
        db.session.query(CustomsDeclaration).delete()
        
        # 2. 清除产品关联 (将 SKU 的 customs_product_id 置空)
        db.session.query(ProductVariant).update({ProductVariant.customs_product_id: None})
        
        # 3. 清除报关品类库
        db.session.query(CustomsProduct).delete()
        db.session.commit()
        click.echo("✅ 已清除报关单数据")
        
    # --- 1. 生成报关品类库 (模拟真实场景) ---
    click.echo("正在生成报关品类库...")
    customs_products_data = [
        {
            "name": "汽车前大灯总成", 
            "hs_code": "8512201000", 
            "rebate_rate": 0.13, 
            "unit": "个", 
            "elements": "品牌|型号|光源类型|适用车型|是否带控制模块",
            "description": "LED前大灯"
        },
        {
            "name": "汽车后尾灯总成", 
            "hs_code": "8512201000", 
            "rebate_rate": 0.13, 
            "unit": "个", 
            "elements": "品牌|型号|光源类型|适用车型",
            "description": "LED尾灯"
        },
        {
            "name": "汽车保险杠", 
            "hs_code": "8708100000", 
            "rebate_rate": 0.13, 
            "unit": "个", 
            "elements": "品牌|适用车型|材质|位置",
            "description": "塑料保险杠"
        },
        {
            "name": "汽车倒车镜", 
            "hs_code": "7009100000", 
            "rebate_rate": 0.13, 
            "unit": "个", 
            "elements": "品牌|适用车型|是否带加热|是否带折叠",
            "description": "后视镜"
        },
        {
            "name": "汽车脚垫", 
            "hs_code": "3926909090", 
            "rebate_rate": 0.13, 
            "unit": "套", 
            "elements": "品牌|材质|适用车型|是否成套",
            "description": "TPE脚垫"
        }
    ]
    
    customs_prods = []
    for cp_data in customs_products_data:
        cp = CustomsProduct(**cp_data)
        db.session.add(cp)
        customs_prods.append(cp)
    db.session.commit()
    click.echo(f"✅ 生成 {len(customs_prods)} 个报关品类")

    products = db.session.query(Product).all()
    if not products:
        click.echo("需要先生成产品数据。")
        return
    
    # 将现有产品随机关联到报关品类 (模拟操作)
    # 注意：这里我们无法直接修改 ProductVariant (SKU)，因为代码中 products 变量获取的是 Product (SPU)
    # 假设每个 SPU 下的所有 Variant 都使用相同的 customs_product
    click.echo("正在关联 SKU 到报关品类...")
    for prod in products:
        # 随机分配一个报关品类
        assigned_cp = random.choice(customs_prods)
        
        # 更新 SPU 下的所有 SKU (ProductVariant)
        for variant in prod.variants:
            variant.customs_product_id = assigned_cp.id
            # 50% 概率设置覆盖中文名
            if random.random() > 0.5:
                variant.customs_name_cn = f"{assigned_cp.name}({prod.brand})"
                
        db.session.add(prod)
    db.session.commit()
    click.echo("✅ 产品关联完成")
        
    company = db.session.query(SysCompany).first()
    if not company:
        # 如果没有公司数据，临时创建一个
        company = SysCompany(name="宁波华瑞逸德电子商务有限公司", code="91330203316935152N")
        db.session.add(company)
        db.session.commit()

    # 获取系统用户列表（用于分配制单人）
    from app.models.user import User
    users = db.session.query(User).filter(User.is_active == True).all()
    if not users:
        click.echo("⚠️  警告：系统中没有活跃用户，created_by 字段将为空")

    fake = Faker('zh_CN')
    
    click.echo(f"正在生成 {count} 条报关单...")
    for i in range(count):
        export_date = date.today() - timedelta(days=random.randint(0, 60))
        declare_date = export_date + timedelta(days=random.randint(1, 3))
        dest_country = random.choice(COUNTRIES)
        
        # 初始化累计值
        fob_total = Decimal(0)
        total_net_weight = Decimal(0)
        total_gross_weight = Decimal(0)
        total_cbm = Decimal(0)
        total_pack_count = 0
        
        # 生成预录入编号 (格式: {公司代码}-YL-{年月}-{流水号})
        year_month = export_date.strftime('%y%m')  # YYMM格式
        sequence = str(i + 1).zfill(4)  # 4位流水号，补0
        pre_entry_no = f"HR-YL-{year_month}-{sequence}"
        
        # 1. 创建报关单头信息
        dec = CustomsDeclaration(
            pre_entry_no=pre_entry_no,
            customs_no="CUS" + datetime.now().strftime('%Y%m') + str(fake.unique.random_number(digits=8)) if random.random() > 0.3 else None,  # 70%概率有报关单单号
            status=random.choice([s.value for s in CustomsStatus]),
            created_by=random.choice(users).id if users else None,  # 随机分配制单人
            
            export_date=export_date,
            declare_date=declare_date,
            filing_no=fake.bothify(text='FILING-####-####'),
            
            internal_shipper_id=company.id,
            overseas_consignee=fake.company() + " INTERNATIONAL INC.",
            trade_mode=random.choice(TRADE_MODES),
            nature_of_exemption=random.choice(EXEMPTION_NATURES),
            license_no=fake.bothify(text='LIC-####-####'),
            
            contract_no=fake.bothify(text='CTR-2025-####'),
            trade_country=dest_country,
            destination_country=dest_country,
            
            transport_mode=random.choice(TRANSPORT_MODES),
            conveyance_ref=fake.bothify(text='VESSEL-#### / V.###'),
            bill_of_lading_no=fake.bothify(text='BL##########'),
            
            loading_port=dest_country + " PORT",
            departure_port=random.choice(PORTS),
            entry_port=random.choice(PORTS),
            
            package_type=random.choice(PACKAGES),
            pack_count=0,  # 将从明细累加
            gross_weight=Decimal(0),  # 将从明细累加
            net_weight=Decimal(0),  # 将从明细累加
            
            transaction_mode=random.choice(['CIF', 'FOB', 'EXW']),
            freight=Decimal('200.00'),
            insurance=Decimal('20.00'),
            incidental=Decimal('0.00'),
            
            marks_and_notes="自排 <CY自行陪同查验> N/M",
            
            fob_total=Decimal(0),
            exchange_rate=Decimal('7.1500'),
            currency=random.choice(CURRENCIES),
            container_mode=random.choice(CONTAINER_MODES),
            version=1,
            is_locked=False
        )
        db.session.add(dec)
        db.session.flush()
        
        # 2. 创建报关单明细 (10-20个，测试长页面滚动)
        num_items = random.randint(10, 20)
        for j in range(num_items):
            prod = random.choice(products) # 这是 SPU
            
            # 随机取一个 SKU
            if not prod.variants:
                continue
            variant = random.choice(prod.variants)
            
            qty = Decimal(random.randint(100, 1000))
            price = Decimal(random.uniform(5, 50)).quantize(Decimal("0.0000"))
            line_total = (qty * price).quantize(Decimal("0.00"))
            
            # 获取报关品类信息 (核心逻辑)
            cp = None
            if variant.customs_product_id:
                cp = db.session.get(CustomsProduct, variant.customs_product_id)
            
            # 确定报关名称 (优先用 SKU 覆盖，否则用品类名，最后兜底)
            final_name = variant.customs_name_cn or (cp.name if cp else prod.name)
            final_hs = cp.hs_code if cp else fake.bothify(text='########')
            final_unit = cp.unit if cp else "007"
            
            # 模拟生成申报要素 (简单拼接)
            spec_str = f"{final_name} | {variant.sku}"
            if cp and cp.elements:
                # 简单模拟填空: 品牌|型号... -> TOYOTA|CAMRY...
                spec_str += " | TOYOTA | CAMRY | LED"
            
            # 生成英文名称（根据产品类型生成）
            en_name_map = {
                "汽车前大灯总成": "Auto Headlight Assembly",
                "汽车后尾灯总成": "Auto Taillight Assembly",
                "汽车保险杠": "Auto Bumper",
                "汽车倒车镜": "Auto Rearview Mirror",
                "汽车脚垫": "Auto Floor Mat"
            }
            en_base_name = en_name_map.get(final_name, "Auto Parts")
            # 添加规格信息到英文名称
            en_spec_str = f"{en_base_name} - {variant.sku}"
            if prod.brand:
                en_spec_str += f" - {prod.brand}"
            
            # 计算重量和体积（模拟真实数据）
            unit_net_weight = Decimal(random.uniform(0.3, 2.5)).quantize(Decimal("0.0001"))  # 单件净重 0.3-2.5kg
            unit_gross_weight = unit_net_weight * Decimal(1.15)  # 毛重=净重*1.15
            
            total_net_weight = (qty * unit_net_weight).quantize(Decimal("0.0000"))
            total_gross_weight = (qty * unit_gross_weight).quantize(Decimal("0.0000"))
            
            # 计算体积 CBM (长宽高随机生成，单位cm，转换为m³)
            length_cm = Decimal(random.uniform(20, 60))  # 20-60cm
            width_cm = Decimal(random.uniform(15, 50))   # 15-50cm
            height_cm = Decimal(random.uniform(10, 40))  # 10-40cm
            cbm_value = (length_cm * width_cm * height_cm / Decimal(1000000)).quantize(Decimal("0.000001"))
            
            # 件数（一箱多件的情况）
            pieces_per_box = random.randint(1, 10)  # 1-10件/箱
            
            item = CustomsDeclarationItem(
                declaration_id=dec.id,
                product_id=prod.id,
                
                item_no=j+1,
                hs_code=final_hs,
                product_name_spec=spec_str,
                product_name_en_spec=en_spec_str,  # 英文名称及规格
                
                qty=qty,
                unit=final_unit, 
            
                qty_2=qty * Decimal(0.8) if random.random() > 0.5 else None,
                unit_2="035" if random.random() > 0.5 else None, # 千克
                
                usd_unit_price=price,
                usd_total=line_total,
                currency='USD',
                
                origin_country='中国',
                final_dest_country=dest_country,
                district_code='330203', # 宁波海曙
                exemption_way='照章征税',
                
                supplier_id=None,
                sku=variant.sku,
                
                # 装箱信息
                box_no=f"C{str(j+1).zfill(3)}",  # C001, C002...
                pack_count=pieces_per_box,  # 件数（一箱多件）
                net_weight=total_net_weight,
                gross_weight=total_gross_weight,
                cbm=cbm_value  # 体积
            )
            db.session.add(item)
            
            # 累加总值到报关单头
            fob_total += line_total
            total_net_weight += item.net_weight
            total_gross_weight += item.gross_weight
            total_cbm += item.cbm
            total_pack_count += item.pack_count
            
        # 更新报关单头信息的汇总数据
        dec.fob_total = fob_total
        dec.net_weight = total_net_weight.quantize(Decimal("0.0000"))
        dec.gross_weight = total_gross_weight.quantize(Decimal("0.0000"))
        dec.pack_count = total_pack_count
        # 注意: cbm 字段仅在 CustomsDeclarationItem 中，头表无需累加
        
    db.session.commit()
    click.echo(f"✅ 成功生成 {count} 条报关单数据")

@click.command('fix-attachment-categories')
def fix_attachment_categories_cmd():
    """修复 customs_attachments 表中的 category 字段值，统一为标准格式"""
    from app.models.customs.attachment import CustomsAttachment
    
    # 旧值到新值的映射
    category_mapping = {
        '01_Basic': '01_Customs',      # 基本单证 -> 关务核心单证
        '02_Container': '03_Logistics', # 货柜单证 -> 物流凭证
        '03_Finance': '02_Trade',       # 财务单证 -> 贸易全套单据
        '04_Others': '04_Others',       # 其他 -> 其他资料（保持不变）
    }
    
    # 标准的 category 值
    valid_categories = ['01_Customs', '02_Trade', '03_Logistics', '04_Others']
    
    click.echo("🔍 开始检查 customs_attachments 表中的 category 字段...")
    
    # 查询所有附件
    all_attachments = db.session.query(CustomsAttachment).all()
    total_count = len(all_attachments)
    updated_count = 0
    
    click.echo(f"📊 共找到 {total_count} 条附件记录")
    
    for att in all_attachments:
        original_category = att.category
        new_category = original_category
        
        # 如果是旧值，转换为新值
        if original_category in category_mapping:
            new_category = category_mapping[original_category]
        # 如果不是标准值，设置为默认值
        elif original_category not in valid_categories:
            new_category = '04_Others'
        
        # 如果需要更新
        if new_category != original_category:
            att.category = new_category
            updated_count += 1
            click.echo(f"  📝 更新附件 ID={att.id}: '{original_category}' -> '{new_category}' (文件: {att.file_name})")
    
    if updated_count > 0:
        db.session.commit()
        click.echo(f"\n✅ 成功更新 {updated_count} 条记录")
    else:
        click.echo("\n✅ 所有记录的 category 字段均已是标准格式，无需更新")
    
    # 显示当前 category 分布统计
    click.echo("\n📊 当前 category 分布统计:")
    from sqlalchemy import func
    category_stats = db.session.query(
        CustomsAttachment.category,
        func.count(CustomsAttachment.id)
    ).group_by(CustomsAttachment.category).all()
    
    category_names = {
        '01_Customs': '关务核心单证',
        '02_Trade': '贸易全套单据',
        '03_Logistics': '物流凭证',
        '04_Others': '其他资料'
    }
    
    for category, count in category_stats:
        category_name = category_names.get(category, '未知分类')
        click.echo(f"  - {category} ({category_name}): {count} 条")

@click.command('test-archived-pdf')
@click.option('--id', default=None, help='报关单ID（默认查找第一个已归档的报关单）')
def test_archived_pdf_cmd(id):
    """测试归档资料PDF生成和合并功能"""
    from app.models.customs import CustomsDeclaration
    from app.services.customs.pdf_service import generate_archived_files_pdf
    from app.models.user import User
    from sqlalchemy.orm import selectinload
    
    # 查找报关单
    if id:
        decl = db.session.query(CustomsDeclaration).options(
            selectinload(CustomsDeclaration.attachments),
            selectinload(CustomsDeclaration.creator),
            selectinload(CustomsDeclaration.internal_shipper)
        ).filter_by(id=id).first()
    else:
        # 查找第一个已归档的报关单
        decl = db.session.query(CustomsDeclaration).options(
            selectinload(CustomsDeclaration.attachments),
            selectinload(CustomsDeclaration.creator),
            selectinload(CustomsDeclaration.internal_shipper)
        ).filter_by(status='archived').first()
    
    if not decl:
        click.echo("❌ 未找到报关单（请确保有已归档的报关单）")
        return
    
    click.echo(f"\n📋 报关单信息:")
    click.echo(f"  ID: {decl.id}")
    click.echo(f"  预录入编号: {decl.pre_entry_no}")
    click.echo(f"  状态: {decl.status}")
    click.echo(f"  附件数量: {len(decl.attachments) if decl.attachments else 0}")
    
    if decl.attachments:
        click.echo(f"\n📎 附件列表:")
        for idx, att in enumerate(decl.attachments, 1):
            click.echo(f"  {idx}. {att.file_name} ({att.file_type}) - {att.category}")
    
    # 获取当前用户
    current_user = db.session.query(User).first()
    
    click.echo(f"\n🔄 开始生成归档资料PDF...")
    
    try:
        pdf_buffer = generate_archived_files_pdf(decl, current_user)
        
        # 保存到临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(pdf_buffer.read())
            tmp_path = tmp.name
        
        click.echo(f"\n✅ PDF生成成功！")
        click.echo(f"📄 临时文件路径: {tmp_path}")
        click.echo(f"💡 提示: 可以手动打开该文件验证内容")
        
    except Exception as e:
        click.echo(f"\n❌ PDF生成失败: {str(e)}")
        import traceback
        click.echo(traceback.format_exc())

@click.command('list-attachments')
def list_attachments_cmd():
    """列出所有报关单及其附件信息"""
    from app.models.customs import CustomsDeclaration
    from sqlalchemy.orm import selectinload
    
    decls = db.session.query(CustomsDeclaration).options(
        selectinload(CustomsDeclaration.attachments)
    ).all()
    
    click.echo(f"\n📊 报关单附件统计:\n")
    
    has_attachments = []
    for decl in decls:
        att_count = len(decl.attachments) if decl.attachments else 0
        if att_count > 0:
            has_attachments.append(decl)
            click.echo(f"  ID: {decl.id:3d} | {decl.pre_entry_no:20s} | 状态: {decl.status:10s} | 附件数: {att_count}")
            for att in decl.attachments:
                click.echo(f"       └─ {att.file_name} ({att.file_type}) - {att.category}")
    
    click.echo(f"\n总计: {len(has_attachments)} 个报关单有附件")

customs_cli.add_command(seed_declarations_cmd)
customs_cli.add_command(fix_attachment_categories_cmd)
customs_cli.add_command(test_archived_pdf_cmd)
customs_cli.add_command(list_attachments_cmd)
