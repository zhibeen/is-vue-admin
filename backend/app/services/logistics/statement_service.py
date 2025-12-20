"""
物流对账单服务层
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.logistics.logistics_statement import LogisticsStatement, StatementStatus, statement_service_relation
from app.models.logistics.shipment_logistics_service import ShipmentLogisticsService, ServiceStatus
from app.models.logistics.logistics_provider import LogisticsProvider
from app.errors import BusinessError


class StatementService:
    """物流对账单服务类"""
    
    @staticmethod
    def generate_statement_no() -> str:
        """生成对账单号: LS + YYYYMMDD + 4位流水号"""
        today = datetime.now().strftime('%Y%m%d')
        prefix = f"LS{today}"
        
        # 查询今日最大流水号
        stmt = select(LogisticsStatement).where(
            LogisticsStatement.statement_no.like(f"{prefix}%")
        ).order_by(LogisticsStatement.statement_no.desc())
        latest = db.session.execute(stmt).scalars().first()
        
        if latest:
            seq = int(latest.statement_no[-4:]) + 1
        else:
            seq = 1
        
        return f"{prefix}{seq:04d}"
    
    @staticmethod
    def create_draft_statement(data: Dict[str, Any], created_by: int) -> LogisticsStatement:
        """
        创建对账单草稿
        
        Args:
            data: {
                'logistics_provider_id': int,
                'period_start': date,
                'period_end': date,
                'auto_include_services': bool  # 是否自动包含该周期内的所有已确认物流服务
            }
            created_by: 创建人ID
        
        Returns:
            LogisticsStatement: 创建的对账单
        """
        provider_id = data['logistics_provider_id']
        period_start = data['period_start']
        period_end = data['period_end']
        
        # 校验物流商是否存在
        provider = db.session.get(LogisticsProvider, provider_id)
        if not provider:
            raise BusinessError('物流服务商不存在', code=404)
        
        # 校验日期
        if period_start > period_end:
            raise BusinessError('对账周期开始日期不能晚于结束日期', code=400)
        
        # 创建对账单
        statement = LogisticsStatement(
            statement_no=StatementService.generate_statement_no(),
            logistics_provider_id=provider_id,
            statement_period_start=period_start,
            statement_period_end=period_end,
            total_amount=Decimal('0'),
            currency='CNY',
            status=StatementStatus.DRAFT.value,
            created_by_id=created_by
        )
        
        db.session.add(statement)
        db.session.flush()  # 获取statement.id
        
        # 自动包含该周期内的物流服务
        if data.get('auto_include_services', False):
            services = StatementService._get_eligible_services(provider_id, period_start, period_end)
            total_amount = Decimal('0')
            
            for service in services:
                # 使用实际费用，如果没有则使用预估费用
                amount = service.actual_amount or service.estimated_amount or Decimal('0')
                total_amount += amount
                
                # 插入关联记录
                db.session.execute(
                    statement_service_relation.insert().values(
                        statement_id=statement.id,
                        logistics_service_id=service.id,
                        reconciled_amount=amount
                    )
                )
            
            statement.total_amount = total_amount
        
        db.session.commit()
        db.session.refresh(statement)
        
        return statement
    
    @staticmethod
    def _get_eligible_services(
        provider_id: int,
        period_start: date,
        period_end: date
    ) -> List[ShipmentLogisticsService]:
        """
        获取符合对账条件的物流服务记录
        
        条件：
        1. 属于指定物流商
        2. 状态为 confirmed（已确认）
        3. 确认时间在对账周期内
        4. 尚未被对账（或部分对账）
        """
        stmt = select(ShipmentLogisticsService).where(
            and_(
                ShipmentLogisticsService.logistics_provider_id == provider_id,
                ShipmentLogisticsService.status == ServiceStatus.CONFIRMED.value,
                ShipmentLogisticsService.confirmed_at >= period_start,
                ShipmentLogisticsService.confirmed_at <= period_end
            )
        ).options(
            selectinload(ShipmentLogisticsService.shipment),
            selectinload(ShipmentLogisticsService.logistics_provider)
        )
        
        services = db.session.execute(stmt).scalars().all()
        return list(services)
    
    @staticmethod
    def add_service_to_statement(
        statement_id: int,
        service_id: int,
        reconciled_amount: Optional[Decimal] = None
    ) -> None:
        """
        添加物流服务到对账单
        
        Args:
            statement_id: 对账单ID
            service_id: 物流服务ID
            reconciled_amount: 对账金额（如果为None，使用服务的实际费用）
        """
        # 校验对账单状态
        statement = db.session.get(LogisticsStatement, statement_id)
        if not statement:
            raise BusinessError('对账单不存在', code=404)
        
        if statement.status != StatementStatus.DRAFT.value:
            raise BusinessError('只有草稿状态的对账单才能修改', code=400)
        
        # 校验物流服务
        service = db.session.get(ShipmentLogisticsService, service_id)
        if not service:
            raise BusinessError('物流服务记录不存在', code=404)
        
        if service.logistics_provider_id != statement.logistics_provider_id:
            raise BusinessError('物流服务商不匹配', code=400)
        
        # 确定对账金额
        if reconciled_amount is None:
            reconciled_amount = service.actual_amount or service.estimated_amount or Decimal('0')
        
        # 插入关联记录
        db.session.execute(
            statement_service_relation.insert().values(
                statement_id=statement_id,
                logistics_service_id=service_id,
                reconciled_amount=reconciled_amount
            )
        )
        
        # 更新对账单总额
        statement.total_amount += reconciled_amount
        db.session.commit()
    
    @staticmethod
    def remove_service_from_statement(statement_id: int, service_id: int) -> None:
        """从对账单中移除物流服务"""
        statement = db.session.get(LogisticsStatement, statement_id)
        if not statement:
            raise BusinessError('对账单不存在', code=404)
        
        if statement.status != StatementStatus.DRAFT.value:
            raise BusinessError('只有草稿状态的对账单才能修改', code=400)
        
        # 获取对账金额
        result = db.session.execute(
            select(statement_service_relation.c.reconciled_amount).where(
                and_(
                    statement_service_relation.c.statement_id == statement_id,
                    statement_service_relation.c.logistics_service_id == service_id
                )
            )
        ).first()
        
        if not result:
            raise BusinessError('该物流服务不在对账单中', code=404)
        
        reconciled_amount = result[0]
        
        # 删除关联记录
        db.session.execute(
            statement_service_relation.delete().where(
                and_(
                    statement_service_relation.c.statement_id == statement_id,
                    statement_service_relation.c.logistics_service_id == service_id
                )
            )
        )
        
        # 更新对账单总额
        statement.total_amount -= reconciled_amount
        db.session.commit()
    
    @staticmethod
    def confirm_statement(statement_id: int, confirmed_by: int) -> LogisticsStatement:
        """
        确认对账单（物流主管）
        
        校验：
        1. 必须上传对账单附件
        2. 关联的物流服务必须都是 confirmed 状态
        3. 总金额必须大于0
        """
        statement = db.session.get(LogisticsStatement, statement_id)
        if not statement:
            raise BusinessError('对账单不存在', code=404)
        
        if statement.status != StatementStatus.DRAFT.value:
            raise BusinessError('只有草稿状态的对账单才能确认', code=400)
        
        # 校验附件
        if not statement.attachment_ids or len(statement.attachment_ids) == 0:
            raise BusinessError('请上传对账单附件（PDF扫描件/Excel）', code=400)
        
        # 校验总金额
        if statement.total_amount <= 0:
            raise BusinessError('对账总额必须大于0', code=400)
        
        # 校验关联的物流服务
        if not statement.logistics_services or len(statement.logistics_services) == 0:
            raise BusinessError('对账单至少需要包含一条物流服务记录', code=400)
        
        # 更新状态
        statement.status = StatementStatus.CONFIRMED.value
        statement.confirmed_by_id = confirmed_by
        statement.confirmed_at = datetime.now()
        
        db.session.commit()
        db.session.refresh(statement)
        
        return statement
    
    @staticmethod
    def submit_to_finance(statement_id: int) -> Dict[str, Any]:
        """
        提交对账单到财务模块
        
        核心逻辑：
        1. 校验对账单状态（必须是 confirmed）
        2. 调用财务模块 Service 创建应付单
        3. 关联对账单与应付单
        4. 更新对账单状态为 submitted
        5. 更新物流服务状态为 reconciled
        """
        from app.services.serc.payable_service import PayableService
        
        # 1. 获取对账单
        statement = db.session.get(LogisticsStatement, statement_id)
        if not statement:
            raise BusinessError('对账单不存在', code=404)
        
        if statement.status != StatementStatus.CONFIRMED.value:
            raise BusinessError('只有已确认的对账单才能提交财务', code=400)
        
        # 2. 准备应付单数据
        provider = statement.logistics_provider
        payable_data = {
            'source_type': 'logistics',
            'source_id': statement.id,
            'source_no': statement.statement_no,
            'payee_type': 'logistics_provider',
            'payee_id': provider.id,
            'payee_name': provider.provider_name,
            'bank_name': provider.bank_name,
            'bank_account': provider.bank_account,
            'bank_account_name': provider.bank_account_name,
            'payable_amount': statement.total_amount,
            'currency': statement.currency,
            'due_date': StatementService._calculate_due_date(provider.settlement_cycle),
            'priority': 3,
            'notes': f'{statement.statement_period_start}至{statement.statement_period_end}物流对账'
        }
        
        # 3. 调用财务模块创建应付单
        payable = PayableService.create_payable(payable_data)
        
        # 4. 更新对账单状态
        statement.finance_payable_id = payable.id
        statement.submitted_to_finance_at = datetime.now()
        statement.status = StatementStatus.SUBMITTED.value
        
        # 5. 更新关联的物流服务状态为 reconciled
        for service in statement.logistics_services:
            service.status = ServiceStatus.RECONCILED.value
            service.reconciled_at = datetime.now()
        
        db.session.commit()
        
        return {
            'statement_id': statement.id,
            'finance_payable_id': payable.id,
            'finance_payable_no': payable.payable_no,
            'submitted_at': statement.submitted_to_finance_at
        }
    
    @staticmethod
    def _calculate_due_date(settlement_cycle: Optional[str]) -> date:
        """根据结算周期计算应付日期"""
        today = date.today()
        
        if settlement_cycle == 'weekly':
            return today + timedelta(days=7)
        elif settlement_cycle == 'monthly':
            return today + timedelta(days=30)
        else:
            # 默认30天
            return today + timedelta(days=30)
    
    @staticmethod
    def get_statement_by_id(statement_id: int) -> Optional[LogisticsStatement]:
        """获取对账单详情（包含关联的物流服务）"""
        stmt = select(LogisticsStatement).where(
            LogisticsStatement.id == statement_id
        ).options(
            selectinload(LogisticsStatement.logistics_provider),
            selectinload(LogisticsStatement.logistics_services).selectinload(ShipmentLogisticsService.shipment),
            selectinload(LogisticsStatement.confirmed_by)
        )
        
        return db.session.execute(stmt).scalars().first()
    
    @staticmethod
    def update_statement(statement_id: int, data: Dict[str, Any]) -> LogisticsStatement:
        """更新对账单（仅草稿状态可修改）"""
        statement = db.session.get(LogisticsStatement, statement_id)
        if not statement:
            raise BusinessError('对账单不存在', code=404)
        
        if statement.status != StatementStatus.DRAFT.value:
            raise BusinessError('只有草稿状态的对账单才能修改', code=400)
        
        # 允许修改的字段
        allowed_fields = ['statement_period_start', 'statement_period_end', 'notes', 'attachment_ids']
        
        for field in allowed_fields:
            if field in data:
                setattr(statement, field, data[field])
        
        db.session.commit()
        db.session.refresh(statement)
        
        return statement
    
    @staticmethod
    def delete_statement(statement_id: int) -> None:
        """删除对账单（仅草稿状态可删除）"""
        statement = db.session.get(LogisticsStatement, statement_id)
        if not statement:
            raise BusinessError('对账单不存在', code=404)
        
        if statement.status != StatementStatus.DRAFT.value:
            raise BusinessError('只有草稿状态的对账单才能删除', code=400)
        
        db.session.delete(statement)
        db.session.commit()

