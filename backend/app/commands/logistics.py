"""
物流模块数据生成命令
生成物流服务商和物流服务明细的模拟数据
"""
import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models.logistics import (
    LogisticsProvider, 
    ShipmentLogisticsService,
    ShipmentOrder
)
from app.models.document import DocumentCenter
from decimal import Decimal
from datetime import datetime, timedelta
import random


@click.group()
def logistics():
    """物流模块相关命令"""
    pass


@logistics.command('init-providers')
@with_appcontext
def init_logistics_providers():
    """初始化物流服务商数据"""
    click.echo('开始生成物流服务商数据...')
    
    providers_data = [
        {
            'provider_name': '顺丰速运',
            'provider_code': 'SF001',
            'service_type': 'domestic_trucking',
            'payment_method': 'postpaid',
            'settlement_cycle': 'monthly',
            'contact_name': '张经理',
            'contact_phone': '13800138001',
            'contact_email': 'zhangmgr@sf-express.com',
            'bank_name': '中国工商银行深圳分行',
            'bank_account': '6222024000012345678',
            'bank_account_name': '深圳顺丰速运有限公司',
            'service_areas': ['广东省', '上海市', '北京市'],
            'is_active': True,
            'notes': '国内领先的快递物流综合服务商'
        },
        {
            'provider_name': '中远海运',
            'provider_code': 'COSCO001',
            'service_type': 'international_sea',
            'payment_method': 'prepaid',
            'settlement_cycle': 'immediate',
            'contact_name': '李船长',
            'contact_phone': '13800138002',
            'contact_email': 'captain.li@cosco.com',
            'bank_name': '中国银行上海分行',
            'bank_account': '6217856000012345678',
            'bank_account_name': '中远海运物流有限公司',
            'service_areas': ['美国', '欧洲', '日本', '东南亚'],
            'is_active': True,
            'notes': '专业的国际海运服务'
        },
        {
            'provider_name': '南方航空货运',
            'provider_code': 'CSN001',
            'service_type': 'international_air',
            'payment_method': 'prepaid',
            'settlement_cycle': 'weekly',
            'contact_name': '王主任',
            'contact_phone': '13800138003',
            'contact_email': 'cargo@csair.com',
            'bank_name': '中国建设银行广州分行',
            'bank_account': '6227002000012345678',
            'bank_account_name': '南方航空货运有限公司',
            'service_areas': ['美国', '欧洲', '澳洲'],
            'is_active': True,
            'notes': '快速的国际空运服务'
        },
        {
            'provider_name': '环球报关行',
            'provider_code': 'GCC001',
            'service_type': 'customs_clearance',
            'payment_method': 'postpaid',
            'settlement_cycle': 'monthly',
            'contact_name': '赵报关',
            'contact_phone': '13800138004',
            'contact_email': 'zhao@globalcustoms.com',
            'bank_name': '招商银行深圳分行',
            'bank_account': '6214830000012345678',
            'bank_account_name': '环球报关服务有限公司',
            'service_areas': ['深圳', '上海', '广州'],
            'is_active': True,
            'notes': '专业的报关清关服务'
        },
        {
            'provider_name': 'UPS快递',
            'provider_code': 'UPS001',
            'service_type': 'destination_delivery',
            'payment_method': 'postpaid',
            'settlement_cycle': 'weekly',
            'contact_name': 'John Smith',
            'contact_phone': '+1-800-742-5877',
            'contact_email': 'john.smith@ups.com',
            'bank_name': 'Bank of America',
            'bank_account': 'US1234567890',
            'bank_account_name': 'United Parcel Service Inc.',
            'service_areas': ['美国', '加拿大'],
            'is_active': True,
            'notes': '美国本土派送服务'
        },
        {
            'provider_name': '德邦物流',
            'provider_code': 'DP001',
            'service_type': 'domestic_trucking',
            'payment_method': 'postpaid',
            'settlement_cycle': 'monthly',
            'contact_name': '陈主管',
            'contact_phone': '13800138005',
            'contact_email': 'chen@deppon.com',
            'bank_name': '中国民生银行上海分行',
            'bank_account': '6226090000012345678',
            'bank_account_name': '德邦物流股份有限公司',
            'service_areas': ['全国'],
            'is_active': True,
            'notes': '国内大型零担快运企业'
        },
    ]
    
    created_count = 0
    for data in providers_data:
        # 检查是否已存在
        existing = LogisticsProvider.query.filter_by(provider_code=data['provider_code']).first()
        if existing:
            click.echo(f'  跳过已存在的服务商: {data["provider_name"]}')
            continue
        
        provider = LogisticsProvider(**data)
        db.session.add(provider)
        created_count += 1
        click.echo(f'  ✓ 创建服务商: {data["provider_name"]} ({data["provider_code"]})')
    
    db.session.commit()
    click.echo(f'\n✓ 完成！共创建 {created_count} 个物流服务商')


@logistics.command('generate-services')
@click.option('--shipment-id', type=int, help='发货单ID（可选，不指定则为所有发货单生成）')
@click.option('--count', default=2, help='每个发货单生成的服务数量')
@with_appcontext
def generate_logistics_services(shipment_id, count):
    """为发货单生成物流服务明细"""
    click.echo('开始生成物流服务明细...')
    
    # 获取所有物流服务商
    providers = LogisticsProvider.query.filter_by(is_active=True).all()
    if not providers:
        click.echo('错误: 请先运行 flask logistics init-providers 创建服务商数据')
        return
    
    # 获取发货单
    if shipment_id:
        shipments = [ShipmentOrder.query.get(shipment_id)]
        if not shipments[0]:
            click.echo(f'错误: 发货单 {shipment_id} 不存在')
            return
    else:
        # 获取最近的10个发货单
        shipments = ShipmentOrder.query.order_by(ShipmentOrder.id.desc()).limit(10).all()
    
    if not shipments:
        click.echo('错误: 没有找到发货单')
        return
    
    service_types = ['domestic_trucking', 'international_sea', 'international_air', 
                     'customs_clearance', 'destination_delivery']
    
    created_count = 0
    for shipment in shipments:
        click.echo(f'\n处理发货单: {shipment.shipment_no}')
        
        # 检查是否已有服务
        existing_count = ShipmentLogisticsService.query.filter_by(shipment_id=shipment.id).count()
        if existing_count > 0:
            click.echo(f'  跳过（已有 {existing_count} 个服务）')
            continue
        
        # 为每个发货单随机选择服务商并生成服务
        selected_providers = random.sample(providers, min(count, len(providers)))
        
        for provider in selected_providers:
            # 生成随机费用
            estimated = Decimal(random.randint(1000, 50000))
            actual = Decimal(int(estimated * random.uniform(0.9, 1.1)))
            
            service = ShipmentLogisticsService(
                shipment_id=shipment.id,
                logistics_provider_id=provider.id,
                service_type=random.choice(service_types),
                service_description=f'{provider.provider_name}提供的物流服务',
                estimated_amount=estimated,
                actual_amount=actual if random.random() > 0.3 else None,  # 30%概率还没有实际费用
                currency='CNY',
                payment_method=provider.payment_method,
                status='confirmed' if random.random() > 0.5 else 'pending',
                notes=f'模拟数据 - {datetime.now().strftime("%Y-%m-%d")}'
            )
            
            # 如果已确认，设置确认时间
            if service.status == 'confirmed':
                service.confirmed_at = datetime.now() - timedelta(days=random.randint(1, 7))
            
            db.session.add(service)
            created_count += 1
            click.echo(f'  ✓ 添加服务: {provider.provider_name} - ¥{estimated:.2f}')
    
    db.session.commit()
    click.echo(f'\n✓ 完成！共创建 {created_count} 条物流服务记录')


@logistics.command('generate-documents')
@click.option('--shipment-id', type=int, help='发货单ID（可选）')
@click.option('--count', default=3, help='每个发货单生成的凭证数量')
@with_appcontext
def generate_documents(shipment_id, count):
    """为发货单生成模拟凭证数据"""
    click.echo('开始生成凭证数据...')
    
    # 获取发货单
    if shipment_id:
        shipments = [ShipmentOrder.query.get(shipment_id)]
        if not shipments[0]:
            click.echo(f'错误: 发货单 {shipment_id} 不存在')
            return
    else:
        # 获取最近的5个发货单
        shipments = ShipmentOrder.query.order_by(ShipmentOrder.id.desc()).limit(5).all()
    
    if not shipments:
        click.echo('错误: 没有找到发货单')
        return
    
    document_types = [
        ('运单', 'waybill', 'service_voucher', '.pdf'),
        ('提单', 'bill_of_lading', 'service_voucher', '.pdf'),
        ('发票', 'invoice', 'invoice_voucher', '.pdf'),
        ('付款凭证', 'payment_proof', 'payment_voucher', '.jpg'),
        ('报关单', 'customs_declaration', 'customs_voucher', '.pdf'),
    ]
    
    created_count = 0
    for shipment in shipments:
        click.echo(f'\n处理发货单: {shipment.shipment_no}')
        
        # 检查是否已有凭证
        existing_count = DocumentCenter.query.filter_by(
            business_type='logistics',
            business_id=shipment.id
        ).count()
        
        if existing_count > 0:
            click.echo(f'  跳过（已有 {existing_count} 个凭证）')
            continue
        
        # 生成凭证
        selected_docs = random.sample(document_types, min(count, len(document_types)))
        
        for doc_name, doc_type, doc_category, file_ext in selected_docs:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = f'{doc_name}_{shipment.shipment_no}_{timestamp}{file_ext}'
            
            document = DocumentCenter(
                business_type='logistics',
                business_id=shipment.id,
                business_no=shipment.shipment_no,
                document_type=doc_type,
                document_category=doc_category,
                file_name=file_name,
                file_path=f'uploads/logistics/{shipment.id}/{file_name}',
                file_size=random.randint(100000, 5000000),  # 100KB - 5MB
                file_type=file_ext,
                file_url=f'/documents/{shipment.id}/{file_name}',
                uploaded_by_id=1,  # 假设管理员用户ID为1
                uploaded_at=datetime.now() - timedelta(days=random.randint(0, 10)),
                audit_status='approved' if random.random() > 0.3 else 'pending',
                archived=False
            )
            
            # 如果已审核，设置审核信息
            if document.audit_status == 'approved':
                document.audited_by_id = 1
                document.audited_at = document.uploaded_at + timedelta(hours=random.randint(1, 48))
            
            db.session.add(document)
            created_count += 1
            click.echo(f'  ✓ 添加凭证: {doc_name} ({file_ext})')
    
    db.session.commit()
    click.echo(f'\n✓ 完成！共创建 {created_count} 个凭证记录')


@logistics.command('clean')
@click.option('--confirm', is_flag=True, help='确认删除')
@with_appcontext
def clean_logistics_data(confirm):
    """清理物流模块的模拟数据"""
    if not confirm:
        click.echo('警告: 此操作将删除所有物流服务商、物流服务明细和相关凭证数据')
        click.echo('请使用 --confirm 参数确认删除')
        return
    
    click.echo('开始清理数据...')
    
    # 删除物流凭证
    doc_count = DocumentCenter.query.filter_by(business_type='logistics').delete()
    click.echo(f'  ✓ 删除 {doc_count} 个凭证')
    
    # 删除物流服务明细
    service_count = ShipmentLogisticsService.query.delete()
    click.echo(f'  ✓ 删除 {service_count} 个物流服务记录')
    
    # 删除物流服务商
    provider_count = LogisticsProvider.query.delete()
    click.echo(f'  ✓ 删除 {provider_count} 个物流服务商')
    
    db.session.commit()
    click.echo('\n✓ 清理完成！')


@logistics.command('stats')
@with_appcontext
def show_logistics_stats():
    """显示物流模块数据统计"""
    click.echo('\n=== 物流模块数据统计 ===\n')
    
    # 物流服务商统计
    total_providers = LogisticsProvider.query.count()
    active_providers = LogisticsProvider.query.filter_by(is_active=True).count()
    click.echo(f'物流服务商: {total_providers} 个（启用: {active_providers}）')
    
    # 物流服务明细统计
    total_services = ShipmentLogisticsService.query.count()
    pending_services = ShipmentLogisticsService.query.filter_by(status='pending').count()
    confirmed_services = ShipmentLogisticsService.query.filter_by(status='confirmed').count()
    click.echo(f'物流服务记录: {total_services} 条')
    click.echo(f'  - 待确认: {pending_services}')
    click.echo(f'  - 已确认: {confirmed_services}')
    
    # 凭证统计
    total_docs = DocumentCenter.query.filter_by(business_type='logistics').count()
    pending_docs = DocumentCenter.query.filter_by(
        business_type='logistics',
        audit_status='pending'
    ).count()
    approved_docs = DocumentCenter.query.filter_by(
        business_type='logistics',
        audit_status='approved'
    ).count()
    click.echo(f'物流凭证: {total_docs} 个')
    click.echo(f'  - 待审核: {pending_docs}')
    click.echo(f'  - 已审核: {approved_docs}')
    
    # 费用统计
    from sqlalchemy import func
    total_estimated = db.session.query(
        func.sum(ShipmentLogisticsService.estimated_amount)
    ).scalar() or 0
    total_actual = db.session.query(
        func.sum(ShipmentLogisticsService.actual_amount)
    ).filter(ShipmentLogisticsService.actual_amount.isnot(None)).scalar() or 0
    
    click.echo(f'\n费用统计:')
    click.echo(f'  - 预估总费用: ¥{total_estimated:,.2f}')
    click.echo(f'  - 实际总费用: ¥{total_actual:,.2f}')
    click.echo()

