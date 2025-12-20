"""
财务应付单服务层
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.serc.payable import FinPayable, FinPaymentPool, PayableStatus, PaymentPoolStatus
from app.errors import BusinessError


class PayableService:
    """财务应付单服务类"""
    
    @staticmethod
    def generate_payable_no() -> str:
        """生成应付单号: AP + YYYYMMDD + 4位流水号"""
        today = datetime.now().strftime('%Y%m%d')
        prefix = f"AP{today}"
        
        # 查询今日最大流水号
        stmt = select(FinPayable).where(
            FinPayable.payable_no.like(f"{prefix}%")
        ).order_by(FinPayable.payable_no.desc())
        latest = db.session.execute(stmt).scalars().first()
        
        if latest:
            seq = int(latest.payable_no[-4:]) + 1
        else:
            seq = 1
        
        return f"{prefix}{seq:04d}"
    
    @staticmethod
    def create_payable(data: Dict[str, Any], created_by: Optional[int] = None) -> FinPayable:
        """
        创建应付单
        
        Args:
            data: {
                'source_type': str,  # supply_contract/logistics/expense
                'source_id': int,
                'source_no': str,
                'payee_type': str,  # supplier/logistics_provider/employee
                'payee_id': int,
                'payee_name': str,
                'bank_name': str (optional),
                'bank_account': str (optional),
                'bank_account_name': str (optional),
                'payable_amount': Decimal,
                'currency': str,
                'due_date': date (optional),
                'priority': int,
                'notes': str (optional)
            }
            created_by: 创建人ID
        
        Returns:
            FinPayable: 创建的应付单
        """
        # 校验必填字段
        required_fields = ['source_type', 'source_id', 'payee_type', 'payee_id', 'payee_name', 'payable_amount']
        for field in required_fields:
            if field not in data:
                raise BusinessError(f'缺少必填字段: {field}', code=400)
        
        # 校验金额
        if data['payable_amount'] <= 0:
            raise BusinessError('应付金额必须大于0', code=400)
        
        # 创建应付单
        payable = FinPayable(
            payable_no=PayableService.generate_payable_no(),
            source_type=data['source_type'],
            source_id=data['source_id'],
            source_no=data.get('source_no'),
            payee_type=data['payee_type'],
            payee_id=data['payee_id'],
            payee_name=data['payee_name'],
            bank_name=data.get('bank_name'),
            bank_account=data.get('bank_account'),
            bank_account_name=data.get('bank_account_name'),
            payable_amount=data['payable_amount'],
            paid_amount=Decimal('0'),
            currency=data.get('currency', 'CNY'),
            due_date=data.get('due_date'),
            priority=data.get('priority', 3),
            status=PayableStatus.PENDING.value,
            notes=data.get('notes'),
            created_by_id=created_by
        )
        
        db.session.add(payable)
        db.session.commit()
        db.session.refresh(payable)
        
        return payable
    
    @staticmethod
    def approve_payable(
        payable_id: int,
        action: str,
        approved_by: int,
        rejection_reason: Optional[str] = None,
        add_to_pool: bool = False,
        pool_id: Optional[int] = None
    ) -> FinPayable:
        """
        审批应付单
        
        Args:
            payable_id: 应付单ID
            action: approve/reject
            approved_by: 审批人ID
            rejection_reason: 驳回原因（驳回时必填）
            add_to_pool: 批准后是否立即加入付款池
            pool_id: 付款池ID（如果add_to_pool=True且未指定，则创建默认池）
        
        Returns:
            FinPayable: 更新后的应付单
        """
        payable = db.session.get(FinPayable, payable_id)
        if not payable:
            raise BusinessError('应付单不存在', code=404)
        
        if payable.status != PayableStatus.PENDING.value:
            raise BusinessError('只有待审批的应付单才能审批', code=400)
        
        if action == 'approve':
            payable.status = PayableStatus.APPROVED.value
            payable.approved_by_id = approved_by
            payable.approved_at = datetime.now()
            
            # 加入付款池
            if add_to_pool:
                if pool_id:
                    pool = db.session.get(FinPaymentPool, pool_id)
                    if not pool:
                        raise BusinessError('付款池不存在', code=404)
                else:
                    # 创建或获取本月默认付款池
                    pool = PayableService._get_or_create_default_pool()
                
                payable.payment_pool_id = pool.id
                payable.status = PayableStatus.IN_POOL.value
                
                # 更新付款池统计
                pool.total_amount += payable.payable_amount
                pool.total_count += 1
        
        elif action == 'reject':
            if not rejection_reason:
                raise BusinessError('驳回时必须填写驳回原因', code=400)
            
            payable.status = PayableStatus.REJECTED.value
            payable.approved_by_id = approved_by
            payable.approved_at = datetime.now()
            payable.rejection_reason = rejection_reason
            
            # 回调通知业务模块（物流对账单）
            if payable.source_type == 'logistics':
                PayableService._notify_logistics_rejection(payable)
        
        else:
            raise BusinessError('无效的审批操作', code=400)
        
        db.session.commit()
        db.session.refresh(payable)
        
        return payable
    
    @staticmethod
    def _get_or_create_default_pool() -> FinPaymentPool:
        """获取或创建本月默认付款池"""
        today = date.today()
        pool_name = f"{today.year}年{today.month}月付款池"
        
        # 查找本月池
        stmt = select(FinPaymentPool).where(
            and_(
                FinPaymentPool.pool_name == pool_name,
                FinPaymentPool.status != PaymentPoolStatus.COMPLETED.value
            )
        )
        pool = db.session.execute(stmt).scalars().first()
        
        if not pool:
            # 创建新池
            pool = FinPaymentPool(
                pool_no=PayableService._generate_pool_no(),
                pool_name=pool_name,
                scheduled_date=today,
                total_amount=Decimal('0'),
                total_count=0,
                status=PaymentPoolStatus.DRAFT.value
            )
            db.session.add(pool)
            db.session.flush()
        
        return pool
    
    @staticmethod
    def _generate_pool_no() -> str:
        """生成付款池编号: PP + YYYYMM + 3位流水号"""
        today = datetime.now().strftime('%Y%m')
        prefix = f"PP{today}"
        
        stmt = select(FinPaymentPool).where(
            FinPaymentPool.pool_no.like(f"{prefix}%")
        ).order_by(FinPaymentPool.pool_no.desc())
        latest = db.session.execute(stmt).scalars().first()
        
        if latest:
            seq = int(latest.pool_no[-3:]) + 1
        else:
            seq = 1
        
        return f"{prefix}{seq:03d}"
    
    @staticmethod
    def _notify_logistics_rejection(payable: FinPayable) -> None:
        """通知物流模块应付单被驳回"""
        from app.models.logistics.logistics_statement import LogisticsStatement, StatementStatus
        
        # 查找对应的对账单
        stmt = select(LogisticsStatement).where(
            LogisticsStatement.id == payable.source_id
        )
        statement = db.session.execute(stmt).scalars().first()
        
        if statement:
            # 回退状态到 confirmed
            statement.status = StatementStatus.CONFIRMED.value
            statement.finance_payable_id = None
            statement.submitted_to_finance_at = None
            # 可以添加驳回记录到 notes
            statement.notes = (statement.notes or '') + f"\n[{datetime.now()}] 财务驳回: {payable.rejection_reason}"
    
    @staticmethod
    def get_payable_by_id(payable_id: int) -> Optional[FinPayable]:
        """获取应付单详情"""
        stmt = select(FinPayable).where(
            FinPayable.id == payable_id
        ).options(
            selectinload(FinPayable.approved_by),
            selectinload(FinPayable.payment_pool),
            selectinload(FinPayable.payment_voucher)
        )
        
        return db.session.execute(stmt).scalars().first()
    
    @staticmethod
    def add_payable_to_pool(payable_id: int, pool_id: int) -> FinPayable:
        """将应付单加入付款池"""
        payable = db.session.get(FinPayable, payable_id)
        if not payable:
            raise BusinessError('应付单不存在', code=404)
        
        if payable.status != PayableStatus.APPROVED.value:
            raise BusinessError('只有已批准的应付单才能加入付款池', code=400)
        
        pool = db.session.get(FinPaymentPool, pool_id)
        if not pool:
            raise BusinessError('付款池不存在', code=404)
        
        if pool.status not in [PaymentPoolStatus.DRAFT.value, PaymentPoolStatus.PENDING.value]:
            raise BusinessError('该付款池已关闭，无法添加新的应付单', code=400)
        
        # 更新应付单
        payable.payment_pool_id = pool_id
        payable.status = PayableStatus.IN_POOL.value
        
        # 更新付款池统计
        pool.total_amount += payable.payable_amount
        pool.total_count += 1
        
        db.session.commit()
        db.session.refresh(payable)
        
        return payable
    
    @staticmethod
    def mark_as_paid(
        payable_id: int,
        paid_amount: Decimal,
        paid_at: Optional[datetime] = None,
        payment_voucher_id: Optional[int] = None
    ) -> FinPayable:
        """
        标记应付单为已付款（由出纳执行）
        
        支持部分付款和全额付款
        """
        payable = db.session.get(FinPayable, payable_id)
        if not payable:
            raise BusinessError('应付单不存在', code=404)
        
        if payable.status not in [PayableStatus.IN_POOL.value, PayableStatus.APPROVED.value]:
            raise BusinessError('只有在付款池中或已批准的应付单才能付款', code=400)
        
        # 校验付款金额
        if paid_amount <= 0:
            raise BusinessError('付款金额必须大于0', code=400)
        
        if payable.paid_amount + paid_amount > payable.payable_amount:
            raise BusinessError('付款金额超过应付金额', code=400)
        
        # 更新付款信息
        payable.paid_amount += paid_amount
        payable.paid_at = paid_at or datetime.now()
        payable.payment_voucher_id = payment_voucher_id
        
        # 判断是否全额付款
        if payable.is_fully_paid:
            payable.status = PayableStatus.PAID.value
            
            # 回调通知业务模块
            if payable.source_type == 'logistics':
                PayableService._notify_logistics_paid(payable)
        
        db.session.commit()
        db.session.refresh(payable)
        
        return payable
    
    @staticmethod
    def _notify_logistics_paid(payable: FinPayable) -> None:
        """通知物流模块应付单已付款"""
        from app.models.logistics.logistics_statement import LogisticsStatement, StatementStatus
        from app.models.logistics.shipment_logistics_service import ServiceStatus
        
        # 更新对账单状态
        stmt = select(LogisticsStatement).where(
            LogisticsStatement.id == payable.source_id
        ).options(
            selectinload(LogisticsStatement.logistics_services)
        )
        statement = db.session.execute(stmt).scalars().first()
        
        if statement:
            statement.status = StatementStatus.PAID.value
            
            # 更新关联的物流服务状态为 paid
            for service in statement.logistics_services:
                service.status = ServiceStatus.PAID.value
                service.paid_at = payable.paid_at

