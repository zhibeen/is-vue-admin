import click
import random
from faker import Faker
from flask.cli import AppGroup
from app.extensions import db
from datetime import datetime, timedelta, date
from decimal import Decimal

serc_cli = AppGroup('serc')

@click.command('seed-soas')
@click.option('--count', default=10, help='尝试生成的SOA数量')
@click.option('--clear', is_flag=True, help='清除现有SOA数据')
def seed_soas_cmd(count, clear):
    """根据现有L1合同生成虚拟SOA (L2结算单)"""
    from app.models.supply import ScmDeliveryContract
    from app.models.serc.finance import FinPurchaseSOA, FinPurchaseSOADetail
    from app.models.purchase.supplier import SysSupplier

    if clear:
        click.echo("正在清除现有SOA数据...")
        db.session.query(FinPurchaseSOADetail).delete()
        db.session.query(FinPurchaseSOA).delete()
        db.session.commit()
        click.echo("✅ 已清除SOA数据")

    # 1. 找到所有未完全结算的合同，或者为了演示，找一些状态合适的合同
    contracts = db.session.query(ScmDeliveryContract).filter(
        ScmDeliveryContract.status.in_(['settling', 'settled'])
    ).all()

    if not contracts:
        click.echo("没有找到合适的L1合同 (ScmDeliveryContract) 来生成 SOA。请先运行 flask supply seed-contracts")
        return

    # 按供应商分组
    contracts_by_supplier = {}
    for c in contracts:
        if c.supplier_id not in contracts_by_supplier:
            contracts_by_supplier[c.supplier_id] = []
        contracts_by_supplier[c.supplier_id].append(c)

    generated_count = 0
    fake = Faker()

    # 对每个供应商生成 1-N 个 SOA
    for supplier_id, supplier_contracts in contracts_by_supplier.items():
        if generated_count >= count:
            break

        # 每次取 1-3 个合同生成一个 SOA
        chunk_size = random.randint(1, 3)
        for i in range(0, len(supplier_contracts), chunk_size):
            if generated_count >= count:
                break
                
            batch_contracts = supplier_contracts[i:i+chunk_size]
            
            # 计算总金额
            total_amount = sum(c.total_amount for c in batch_contracts)
            
            soa_no = f"SOA-{datetime.now().strftime('%Y%m')}-{fake.unique.random_number(digits=6)}"
            
            soa = FinPurchaseSOA(
                soa_no=soa_no,
                supplier_id=supplier_id,
                period_start=date(datetime.now().year, datetime.now().month, 1),
                period_end=date(datetime.now().year, datetime.now().month, 28),
                total_payable=total_amount,
                currency='CNY', # 假设
                status=random.choice(['draft', 'confirmed', 'approved']),
                payment_status='unpaid',
                invoice_status='none'
            )
            
            db.session.add(soa)
            db.session.flush() # 获取 ID
            
            # 生成 Details
            for contract in batch_contracts:
                detail = FinPurchaseSOADetail(
                    soa_id=soa.id,
                    l1_contract_id=contract.id,
                    amount=contract.total_amount
                )
                db.session.add(detail)
            
            generated_count += 1
            
    db.session.commit()
    click.echo(f"✅ 成功生成 {generated_count} 条 SOA 数据")


@click.command('seed-pool')
@click.option('--clear', is_flag=True, help='清除现有资金池数据')
def seed_pool_cmd(clear):
    """根据现有SOA生成虚拟资金池条目 (L3 Payment Pool)"""
    from app.models.serc.finance import FinPurchaseSOA, FinPaymentPoolOld

    if clear:
        click.echo("正在清除现有资金池数据...")
        db.session.query(FinPaymentPoolOld).delete()
        db.session.commit()
        click.echo("✅ 已清除资金池数据")

    # 找到所有 approved 的 SOA
    soas = db.session.query(FinPurchaseSOA).filter_by(status='approved').all()
    
    if not soas:
        click.echo("没有找到状态为 approved 的 SOA。尝试生成更多 SOA 或手动更新状态。")
        # 为了演示，如果没有 approved 的，就拿 confirmed 的
        soas = db.session.query(FinPurchaseSOA).filter_by(status='confirmed').all()

    if not soas:
        click.echo("没有找到可用的 SOA 数据。请先运行 flask serc seed-soas")
        return

    count = 0
    for soa in soas:
        # 检查是否已经在池子里
        exists = db.session.query(FinPaymentPoolOld).filter_by(soa_id=soa.id).first()
        if exists:
            continue
            
        pool_item = FinPaymentPoolOld(
            soa_id=soa.id,
            amount=soa.total_payable,
            currency=soa.currency,
            due_date=date.today() + timedelta(days=random.randint(5, 30)),
            priority=random.randint(1, 100),
            status='pending_approval',
            type='goods'
        )
        db.session.add(pool_item)
        count += 1
        
    db.session.commit()
    click.echo(f"✅ 成功生成 {count} 条资金池数据")


@click.command('seed-invoices')
@click.option('--count', default=20, help='生成发票数量')
@click.option('--clear', is_flag=True, help='清除现有发票数据')
def seed_invoices_cmd(count, clear):
    """生成虚拟进项发票 (TaxInvoice)"""
    from app.models.serc.tax import TaxInvoice, TaxInvoiceItem
    from app.models.serc.finance import FinPurchaseSOA

    if clear:
        click.echo("正在清除现有发票数据...")
        db.session.query(TaxInvoiceItem).delete()
        db.session.query(TaxInvoice).delete()
        db.session.commit()
        click.echo("✅ 已清除发票数据")

    # 尝试关联到 SOA
    soas = db.session.query(FinPurchaseSOA).all()
    
    fake = Faker()
    
    for i in range(count):
        soa = random.choice(soas) if soas and random.random() > 0.3 else None
        
        amount = Decimal(random.randint(1000, 50000))
        tax_rate = Decimal('0.13')
        tax_amount = amount * tax_rate
        total_amount = amount + tax_amount
        
        invoice = TaxInvoice(
            invoice_code=str(fake.random_number(digits=10)),
            invoice_no=str(fake.unique.random_number(digits=8)),
            amount_total=total_amount,
            tax_amount=tax_amount,
            soa_id=soa.id if soa else None,
            status=random.choice(['free', 'matched', 'archived'])
        )
        db.session.add(invoice)
        db.session.flush()
        
        # 生成一个 Item
        item = TaxInvoiceItem(
            invoice_id=invoice.id,
            name="模拟商品 " + fake.word(),
            unit="个",
            qty=Decimal(random.randint(10, 100)),
            price=amount / Decimal(10), # 简单估算
            total=amount,
            # tax_rate...
        )
        db.session.add(item)
        
    db.session.commit()
    click.echo(f"✅ 成功生成 {count} 条进项发票数据")


serc_cli.add_command(seed_soas_cmd)
serc_cli.add_command(seed_pool_cmd)
serc_cli.add_command(seed_invoices_cmd)
