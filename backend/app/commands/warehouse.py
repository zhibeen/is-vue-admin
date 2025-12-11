import click
from flask.cli import with_appcontext
from sqlalchemy import text
import random
from datetime import datetime, timedelta
from decimal import Decimal
from app.extensions import db
from app.models.warehouse.warehouse import Warehouse, WarehouseLocation
from app.models.warehouse.stock import WarehouseStock, WarehouseStockMovement
from app.models.warehouse.policy import WarehouseProductGroup, WarehouseProductGroupItem, StockAllocationPolicy
from app.models.warehouse.third_party import WarehouseThirdPartyService, WarehouseThirdPartyWarehouse
from app.models.product import ProductVariant  # Use ProductVariant instead of Item for SKU source

def clear_data():
    """清除现有仓库相关数据"""
    click.echo("正在清除现有仓库及库存数据...")
    
    # Disable foreign key checks temporarily if needed, but safer to delete in order
    db.session.execute(text("TRUNCATE TABLE stock_movements RESTART IDENTITY CASCADE"))
    db.session.execute(text("TRUNCATE TABLE stocks RESTART IDENTITY CASCADE"))
    db.session.execute(text("TRUNCATE TABLE stock_discrepancies RESTART IDENTITY CASCADE"))
    db.session.execute(text("TRUNCATE TABLE warehouse_locations RESTART IDENTITY CASCADE"))
    db.session.execute(text("TRUNCATE TABLE stock_allocation_policies RESTART IDENTITY CASCADE"))
    db.session.execute(text("TRUNCATE TABLE warehouse_product_group_items RESTART IDENTITY CASCADE"))
    db.session.execute(text("TRUNCATE TABLE warehouse_product_groups RESTART IDENTITY CASCADE"))
    db.session.execute(text("TRUNCATE TABLE warehouse_third_party_sku_mappings RESTART IDENTITY CASCADE"))
    db.session.execute(text("TRUNCATE TABLE warehouse_third_party_warehouse_maps RESTART IDENTITY CASCADE"))
    db.session.execute(text("TRUNCATE TABLE warehouse_third_party_warehouses RESTART IDENTITY CASCADE"))
    db.session.execute(text("TRUNCATE TABLE warehouse_third_party_services RESTART IDENTITY CASCADE"))
    
    # We might not want to delete ALL warehouses if they are referenced by other things, 
    # but for a full rebuild/seed, we usually do.
    # Check if we should delete warehouses. Let's delete only those we created or all.
    # For this script, let's assume we own the warehouse table.
    db.session.execute(text("TRUNCATE TABLE warehouses RESTART IDENTITY CASCADE"))
    
    db.session.commit()
    click.echo("数据清除完成。")

def create_third_party_services():
    """创建第三方服务商配置及模拟远程仓库"""
    click.echo("正在创建第三方服务商配置...")
    
    # 1. 创建服务商
    # 先检查是否存在，避免重复插入
    svc_gc = db.session.query(WarehouseThirdPartyService).filter_by(code='goodcang').first()
    if not svc_gc:
        svc_gc = WarehouseThirdPartyService(
            code='goodcang',
            name='谷仓海外仓',
            api_url='https://api.goodcang.com/v1',
            app_key='mock_gc_app_key',
            app_secret='mock_gc_secret',
            config_template={'sandbox': True}
        )
        db.session.add(svc_gc)
    
    svc_winit = db.session.query(WarehouseThirdPartyService).filter_by(code='winit').first()
    if not svc_winit:
        svc_winit = WarehouseThirdPartyService(
            code='winit',
            name='万邑通',
            api_url='https://api.winit.com/v1',
            app_key='mock_winit_app_key',
            app_secret='mock_winit_secret',
            config_template={'sandbox': True}
        )
        db.session.add(svc_winit)
    
    db.session.flush() # get IDs
    
    # 2. 创建模拟的三方仓库列表 (WarehouseThirdPartyWarehouse)
    # 这些是用户点击"全量同步"后会拉取下来的数据
    
    # 谷仓 (20个)
    gc_warehouses = []
    for i in range(1, 21):
        code = f'GC-US-{i:03d}'
        if not db.session.query(WarehouseThirdPartyWarehouse).filter_by(service_id=svc_gc.id, code=code).first():
            gc_warehouses.append(
                WarehouseThirdPartyWarehouse(service_id=svc_gc.id, code=code, name=f'谷仓美东{i}号仓', country_code='US', is_active=True)
            )
    
    # 万邑通 (20个)
    winit_warehouses = []
    for i in range(1, 21):
        code = f'WI-DE-{i:03d}'
        if not db.session.query(WarehouseThirdPartyWarehouse).filter_by(service_id=svc_winit.id, code=code).first():
            winit_warehouses.append(
                WarehouseThirdPartyWarehouse(service_id=svc_winit.id, code=code, name=f'万邑通德国{i}号仓', country_code='DE', is_active=True)
            )
    
    db.session.add_all(gc_warehouses)
    db.session.add_all(winit_warehouses)
    
    db.session.commit()
    click.echo(f"创建或更新了第三方服务商 和 {len(gc_warehouses) + len(winit_warehouses)} 个三方仓库。")
    return {'goodcang': svc_gc, 'winit': svc_winit, 'gc_whs': gc_warehouses}

def create_warehouses(gc_svc=None, gc_whs=None):
    """创建基础仓库"""
    click.echo("正在创建仓库...")
    
    warehouses = [
        # 1. 国内自营总仓 (实体/国内/自营)
        Warehouse(
            code='CN-MAIN',
            name='中国华南总仓',
            category='physical',
            location_type='domestic',
            ownership_type='self',
            status='active',
            business_type='standard',
            currency='CNY',
            timezone='Asia/Shanghai',
            capacity=10000.0,
            address='广东省广州市白云区XX路1号',
            contact_person='张三',
            contact_phone='13800138000'
        ),
        # 2. 美国洛杉矶三方仓 (实体/海外/三方) - 谷仓
        Warehouse(
            code='US-LA',
            name='美国洛杉矶仓 (GoodCang)',
            category='physical',
            location_type='overseas',
            ownership_type='third_party',
            status='active',
            business_type='standard',
            currency='USD',
            timezone='America/Los_Angeles',
            third_party_service_id=gc_svc.id if gc_svc else None,
            third_party_warehouse_id=gc_whs[1].id if gc_whs and len(gc_whs) > 1 else None,
            api_config={"provider": "goodcang", "external_code": "US_LA_001"} 
        ),
        # 3. 德国法兰克福仓 (实体/海外/三方) - 万邑通
        Warehouse(
            code='DE-FRA',
            name='德国法兰克福仓 (Winit)',
            category='physical',
            location_type='overseas',
            ownership_type='third_party',
            status='active',
            business_type='standard',
            currency='EUR',
            timezone='Europe/Berlin',
            api_config={"provider": "winit", "external_code": "DE_FRA_001"}
        ),
        # 4. FBA US (实体/海外/三方) - Amazon Fulfillment
        Warehouse(
            code='FBA-US',
            name='Amazon FBA US',
            category='physical',
            location_type='overseas',
            ownership_type='third_party',
            status='active',
            business_type='fba',
            currency='USD',
            timezone='America/New_York'
        ),
        # 5. 销售虚拟仓 - Amazon US (虚拟/海外/自营) - 销售端缓冲
        Warehouse(
            code='VIR-AMZ-US',
            name='Amazon US 销售虚拟仓',
            category='virtual',
            location_type='overseas',
            ownership_type='self',
            status='active',
            business_type='sales_channel',
            currency='USD',
            # 这里的 child_warehouse_ids 可以用于聚合显示实际库存来源，例如聚合 FBA 和 US-LA
            # 但实际逻辑由 AllocationPolicy 决定。这里仅做示例。
            # 假设 ID 2=US-LA, 4=FBA-US (需要实际运行后获得的ID，这里先留空或仅做标记)
        ),
        # 6. 销售虚拟仓 - Shopify (虚拟/国内/自营) - 销售端缓冲
        Warehouse(
            code='VIR-SHOPIFY',
            name='Shopify 独立站虚拟仓',
            category='virtual',
            location_type='domestic', 
            ownership_type='self',
            status='active',
            business_type='sales_channel',
            currency='USD'
        ),
        # 7. 采购虚拟仓 (虚拟/国内/自营) - 采购端缓冲
        Warehouse(
            code='VIR-PURCHASE',
            name='采购计划缓冲仓',
            category='virtual',
            location_type='domestic',
            ownership_type='self',
            status='planning', # 状态为筹备中或active
            business_type='planning',
            currency='CNY'
        ),
        # 8. 废弃仓库示例
        Warehouse(
            code='CN-OLD',
            name='旧广州仓 (已搬迁)',
            category='physical',
            location_type='domestic',
            ownership_type='self',
            status='deprecated',
            business_type='standard',
            currency='CNY'
        )
    ]
    
    db.session.add_all(warehouses)
    db.session.commit()
    click.echo(f"创建了 {len(warehouses)} 个仓库。")
    return {w.code: w for w in warehouses}

def create_locations(cn_warehouse):
    """为国内仓生成库位"""
    click.echo(f"正在为 {cn_warehouse.name} 生成库位...")
    locations = []
    
    # 简单的库位生成: A区 01-05排 01-03层 01-10位
    # 为了演示，只生成少量
    for aisle in range(1, 4): # 3 Aisles
    # ... code truncated for brevity ...
        for shelf in range(1, 4): # 3 Shelves
            for bin_loc in range(1, 6): # 5 Bins
                code = f"A-{aisle:02d}-{shelf:02d}-{bin_loc:02d}"
                loc = WarehouseLocation(
                    warehouse_id=cn_warehouse.id,
                    code=code,
                    type='storage',
                    is_locked=False,
                    allow_mixing=True
                )
                locations.append(loc)
    
    # 添加几个特殊区域
    locations.append(WarehouseLocation(warehouse_id=cn_warehouse.id, code='STAGE-IN', type='receive'))
    locations.append(WarehouseLocation(warehouse_id=cn_warehouse.id, code='STAGE-OUT', type='pick'))
    
    db.session.add_all(locations)
    db.session.commit()
    click.echo(f"生成了 {len(locations)} 个库位。")
    return locations

def create_stock_and_movements(warehouses, skus, locations):
    """生成初始库存和流水"""
    click.echo("正在生成库存数据...")
    
    movements = []
    stocks = []
    
    cn_wh = warehouses['CN-MAIN']
    us_wh = warehouses['US-LA']
    de_wh = warehouses['DE-FRA']
    fba_wh = warehouses['FBA-US']
    
    # 随机选一些 SKU 有库存
    active_skus = skus[:100] if len(skus) > 100 else skus
    
    for sku in active_skus:
        # --- 1. CN-MAIN (国内总仓 - 基础库存) ---
        qty_cn_in = random.randint(100, 1000) # 初始大货入库
        
        # 入库流水 (30-60天前)
        mv_in = WarehouseStockMovement(
            sku=sku,
            warehouse_id=cn_wh.id,
            location_id=random.choice(locations).id if locations else None,
            order_type='inbound',
            order_no=f"PO-{datetime.now().strftime('%Y%m')}-{random.randint(1000,9999)}",
            quantity_delta=qty_cn_in,
            unit_cost=Decimal(random.uniform(5.0, 50.0)),
            currency='CNY',
            status='confirmed',
            created_at=datetime.utcnow() - timedelta(days=random.randint(30, 60))
        )
        movements.append(mv_in)

        # 模拟销售出库 (Outbound) - 消耗 0-20% 库存
        qty_sold_cn = random.randint(0, int(qty_cn_in * 0.2))
        if qty_sold_cn > 0:
            mv_out = WarehouseStockMovement(
                sku=sku,
                warehouse_id=cn_wh.id,
                order_type='outbound',
                order_no=f"SO-CN-{random.randint(10000,99999)}",
                quantity_delta=-qty_sold_cn,
                unit_cost=mv_in.unit_cost, # 简化成本
                currency='CNY',
                status='confirmed',
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 20))
            )
            movements.append(mv_out)
        
        current_cn_qty = qty_cn_in - qty_sold_cn

        # --- 2. 调拨 (Transfer) CN -> Overseas ---
        # 50% 概率发生调拨
        if random.random() > 0.5:
            # 调拨 10-30% 到海外仓
            qty_transfer = random.randint(10, int(current_cn_qty * 0.3))
            target_wh = random.choice([us_wh, fba_wh, de_wh])
            
            # 国内仓调出
            mv_trans_out = WarehouseStockMovement(
                sku=sku,
                warehouse_id=cn_wh.id,
                order_type='transfer_out',
                order_no=f"TO-{random.randint(1000,9999)}",
                quantity_delta=-qty_transfer,
                status='confirmed',
                created_at=datetime.utcnow() - timedelta(days=15)
            )
            movements.append(mv_trans_out)
            current_cn_qty -= qty_transfer

            # 海外仓调入 (假设已到货)
            mv_trans_in = WarehouseStockMovement(
                sku=sku,
                warehouse_id=target_wh.id,
                order_type='transfer_in',
                order_no=f"TI-{random.randint(1000,9999)}", 
                quantity_delta=qty_transfer,
                status='confirmed',
                created_at=datetime.utcnow() - timedelta(days=2)
            )
            movements.append(mv_trans_in)
            
            # 生成海外仓库存记录
            stock_target = WarehouseStock(
                sku=sku,
                warehouse_id=target_wh.id,
                physical_quantity=qty_transfer,
                available_quantity=qty_transfer,
                version=1
            )
            stocks.append(stock_target)

        # --- 3. 生成国内仓最终库存记录 ---
        stock_cn = WarehouseStock(
            sku=sku,
            warehouse_id=cn_wh.id,
            physical_quantity=current_cn_qty,
            available_quantity=current_cn_qty,
            version=1
        )
        stocks.append(stock_cn)

    db.session.add_all(stocks)
    db.session.add_all(movements)
    db.session.commit()
    click.echo(f"生成了 {len(stocks)} 条库存余额记录和 {len(movements)} 条库存流水。")
    return active_skus

def create_discrepancies(warehouses, skus):
    """生成差异单数据 (模拟第三方仓同步差异)"""
    click.echo("正在生成同步差异数据...")
    from app.models.warehouse.stock import WarehouseStockDiscrepancy
    
    us_wh = warehouses['US-LA']
    active_skus = skus[:10]
    discrepancies = []
    
    for sku in active_skus:
        # 模拟 30% 概率出现差异
        if random.random() > 0.7:
            local_qty = random.randint(50, 100)
            remote_qty = local_qty + random.randint(-5, 5) # 少量差异
            
            if local_qty == remote_qty:
                remote_qty += 1 # 强制差异
                
            disc = WarehouseStockDiscrepancy(
                warehouse_id=us_wh.id,
                sku=sku,
                local_qty=local_qty,
                remote_qty=remote_qty,
                diff_ratio=round(abs(remote_qty - local_qty) / local_qty, 4) if local_qty > 0 else 1.0,
                status='pending',
                discovered_at=datetime.utcnow() - timedelta(hours=random.randint(1, 24))
            )
            discrepancies.append(disc)
            
    if discrepancies:
        db.session.add_all(discrepancies)
        db.session.commit()
        click.echo(f"生成了 {len(discrepancies)} 条库存差异记录。")
    else:
        click.echo("未生成差异记录 (随机跳过)。")

def create_allocation_policies(warehouses, skus):
    """生成分配策略"""
    click.echo("正在生成库存分配策略...")
    
    # 1. 创建一个 SKU 组
    group = WarehouseProductGroup(
        code='G-2025-SPRING',
        name='2025 Spring Sale Collection',
        note='High priority items for spring sale'
    )
    db.session.add(group)
    db.session.flush() # get ID
    
    # 添加一些 SKU 到组
    group_skus = skus[:10]
    for sku in group_skus:
        item = WarehouseProductGroupItem(group_id=group.id, sku=sku)
        db.session.add(item)
    
    # 2. 策略: 该组商品优先分配给 Amazon US
    policy1 = StockAllocationPolicy(
        virtual_warehouse_id=warehouses['VIR-AMZ-US'].id,
        warehouse_product_group_id=group.id,
        ratio=0.9, # 90% allocation
        priority=100,
        policy_mode='override'
    )
    db.session.add(policy1)
    
    # 3. 策略: Shopify 默认获取 CN-MAIN 所有库存
    policy2 = StockAllocationPolicy(
        virtual_warehouse_id=warehouses['VIR-SHOPIFY'].id,
        source_warehouse_id=warehouses['CN-MAIN'].id,
        ratio=1.0,
        priority=10,
        policy_mode='override'
    )
    db.session.add(policy2)
    
    db.session.commit()
    click.echo("策略生成完成。")

def create_sku_mappings(gc_svc, gc_wh, skus):
    """创建三方SKU映射 (v1.4 新增)"""
    click.echo("正在创建SKU映射...")
    from app.models.warehouse.third_party import WarehouseThirdPartySkuMapping
    
    mappings = []
    # 以前10个SKU为例
    target_skus = skus[:10]
    
    for sku in target_skus:
        # Level 2: 服务商级映射 (全局)
        # 假设远程 SKU 前缀为 'R-'
        m2 = WarehouseThirdPartySkuMapping(
            service_id=gc_svc.id,
            warehouse_id=None, # Global
            remote_sku=f"R-{sku}",
            local_sku=sku,
            quantity_ratio=1.0,
            priority=10
        )
        mappings.append(m2)
        
        # Level 3: 仓库级映射 (特例) - 针对某个仓库
        if gc_wh:
             m3 = WarehouseThirdPartySkuMapping(
                service_id=gc_svc.id,
                warehouse_id=gc_wh.id,
                remote_sku=f"R-{sku}-WH", # 特殊后缀
                local_sku=sku,
                quantity_ratio=1.0,
                priority=5 # 数字越小优先级越高? 代码说是 default=0, 但通常越小越高
            )
             mappings.append(m3)
             
    if mappings:
        db.session.add_all(mappings)
        db.session.commit()
        click.echo(f"生成了 {len(mappings)} 条SKU映射关系。")
    else:
        click.echo("未生成 SKU 映射 (无 SKU)。")

def create_unmapped_sku_mappings(gc_svc, skus):
    """创建一些未配对的三方SKU (用于演示配对功能)"""
    click.echo("正在创建未配对的三方商品...")
    from app.models.warehouse.third_party import WarehouseThirdPartyProduct
    
    products = []
    # 模拟 20 个三方商品
    for i in range(1, 21):
        remote_sku = f"MOCK-REMOTE-{i:03d}"
        
        # 避免重复
        exists = db.session.query(WarehouseThirdPartyProduct).filter_by(
            service_id=gc_svc.id, 
            remote_sku=remote_sku
        ).first()
        
        if not exists:
            products.append(WarehouseThirdPartyProduct(
                service_id=gc_svc.id,
                remote_sku=remote_sku,
                remote_name=f"Mock Remote Product {i}",
                specs={"weight": 1.5, "dim": [10, 10, 10]}
            ))
            
    if products:
        db.session.add_all(products)
        db.session.commit()
        click.echo(f"创建了 {len(products)} 个三方商品源数据。")
    else:
        click.echo("没有创建新的三方商品 (已存在)。")



@click.group('warehouse', help='仓库模块管理命令')
def warehouse_cli():
    pass

@warehouse_cli.command('seed-warehouse')
@click.option('--clear', is_flag=True, help='清除现有数据')
@with_appcontext
def seed_warehouse_command(clear):
    """生成仓库模块模拟数据"""
    
    if clear:
        clear_data()
    
    # 0. Third Party Services & Mock Remote Warehouses
    tp_data = create_third_party_services()
    gc_svc = tp_data['goodcang']
    gc_whs = tp_data['gc_whs']

    # 1. Warehouses
    wh_map = create_warehouses(gc_svc, gc_whs)
    
    # 2. Locations
    locs = create_locations(wh_map['CN-MAIN'])
    
    # 3. Get existing SKUs from ProductVariant
    # We need to ensure there are products first. 
    # If not, we might fail or need to mock SKUs.
    from sqlalchemy.exc import ProgrammingError
    try:
        variants = db.session.query(ProductVariant).limit(100).all()
        skus = [v.sku for v in variants if v.sku]
    except ProgrammingError:
        db.session.rollback()
        skus = []
    
    if not skus:
        click.echo("警告: 未找到产品 SKU。请先运行 'flask product seed-products'。")
        click.echo("生成一些虚拟 SKU 用于测试...")
        skus = [f"TEST-SKU-{i:03d}" for i in range(1, 21)]
        
    # 4. Stocks
    active_skus = create_stock_and_movements(wh_map, skus, locs)
    
    # 4.5 Discrepancies
    create_discrepancies(wh_map, active_skus)

    # 4.6 SKU Mappings
    if gc_whs and len(gc_whs) > 0:
        create_sku_mappings(gc_svc, gc_whs[0], skus)
    
    # 4.7 Mock 3rd-party product list (Unified Product Table) - optional/future
    # For now, we rely on SKU Mappings to know "what SKUs exist remotely".
    # But ideally, we should have a `WarehouseThirdPartyProduct` table.
    
    # 4.8 Mock Unmapped 3rd-party products (simulate remote products waiting for mapping)
    create_unmapped_sku_mappings(gc_svc, skus)
    
    # 5. Policies
    create_allocation_policies(wh_map, active_skus)
    
    click.echo("✅ 仓库模块数据初始化完成!")
