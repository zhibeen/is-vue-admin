"""
发货单物流服务明细服务层
处理物流服务的添加、更新、确认、对账等业务逻辑
"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.logistics.shipment_logistics_service import ShipmentLogisticsService, ServiceStatus
from app.models.logistics.shipment import ShipmentOrder
from app.models.logistics.logistics_provider import LogisticsProvider
from app.extensions import db
from app.errors import BusinessError


class ShipmentLogisticsServiceService:
    """物流服务明细业务逻辑类"""
    
    @staticmethod
    def add_service(shipment_id: int, data: dict) -> ShipmentLogisticsService:
        """
        为发货单添加物流服务
        
        Args:
            shipment_id: 发货单ID
            data: 物流服务数据
            
        Returns:
            创建的物流服务对象
            
        Raises:
            BusinessError: 当发货单不存在或服务商不存在时
        """
        # 验证发货单存在
        shipment = db.session.get(ShipmentOrder, shipment_id)
        if not shipment:
            raise BusinessError('发货单不存在', code=404)
        
        # 验证物流服务商存在
        provider = db.session.get(LogisticsProvider, data['logistics_provider_id'])
        if not provider:
            raise BusinessError('物流服务商不存在', code=404)
        
        # 创建物流服务
        service = ShipmentLogisticsService(
            shipment_id=shipment_id,
            **data
        )
        db.session.add(service)
        db.session.commit()
        db.session.refresh(service)
        
        return service
    
    @staticmethod
    def get_service_by_id(service_id: int) -> Optional[ShipmentLogisticsService]:
        """
        根据ID获取物流服务
        
        Args:
            service_id: 物流服务ID
            
        Returns:
            物流服务对象或None
        """
        stmt = select(ShipmentLogisticsService).where(
            ShipmentLogisticsService.id == service_id
        ).options(
            selectinload(ShipmentLogisticsService.logistics_provider)
        )
        return db.session.execute(stmt).scalar_one_or_none()
    
    @staticmethod
    def get_services_by_shipment(shipment_id: int) -> List[ShipmentLogisticsService]:
        """
        获取发货单的所有物流服务
        
        Args:
            shipment_id: 发货单ID
            
        Returns:
            物流服务列表
        """
        stmt = select(ShipmentLogisticsService).where(
            ShipmentLogisticsService.shipment_id == shipment_id
        ).options(
            selectinload(ShipmentLogisticsService.logistics_provider)
        ).order_by(ShipmentLogisticsService.id)
        
        return db.session.execute(stmt).scalars().all()
    
    @staticmethod
    def update_service(service_id: int, data: dict) -> ShipmentLogisticsService:
        """
        更新物流服务
        
        Args:
            service_id: 物流服务ID
            data: 更新数据
            
        Returns:
            更新后的物流服务对象
            
        Raises:
            BusinessError: 当物流服务不存在时
        """
        service = ShipmentLogisticsServiceService.get_service_by_id(service_id)
        if not service:
            raise BusinessError('物流服务不存在', code=404)
        
        # 更新字段
        for key, value in data.items():
            if hasattr(service, key):
                setattr(service, key, value)
        
        db.session.commit()
        db.session.refresh(service)
        
        return service
    
    @staticmethod
    def delete_service(service_id: int) -> None:
        """
        删除物流服务
        
        Args:
            service_id: 物流服务ID
            
        Raises:
            BusinessError: 当物流服务不存在或已对账时
        """
        service = ShipmentLogisticsServiceService.get_service_by_id(service_id)
        if not service:
            raise BusinessError('物流服务不存在', code=404)
        
        # 如果已对账或已付款，不允许删除
        if service.status in [ServiceStatus.RECONCILED.value, ServiceStatus.PAID.value]:
            raise BusinessError('已对账或已付款的服务不能删除', code=400)
        
        db.session.delete(service)
        db.session.commit()
    
    @staticmethod
    def calculate_total_cost(shipment_id: int, use_actual: bool = True) -> Decimal:
        """
        计算发货单的物流总费用
        
        Args:
            shipment_id: 发货单ID
            use_actual: 是否使用实际费用（True=actual_amount优先，False=estimated_amount）
            
        Returns:
            物流总费用
        """
        services = ShipmentLogisticsServiceService.get_services_by_shipment(shipment_id)
        
        total = Decimal('0.00')
        for service in services:
            if use_actual:
                # 优先使用实际费用，如果没有则使用预估费用
                amount = service.actual_amount or service.estimated_amount or Decimal('0.00')
            else:
                # 使用预估费用
                amount = service.estimated_amount or Decimal('0.00')
            
            total += amount
        
        return total
    
    @staticmethod
    def confirm_service(service_id: int) -> ShipmentLogisticsService:
        """
        确认物流服务
        
        Args:
            service_id: 物流服务ID
            
        Returns:
            更新后的物流服务对象
            
        Raises:
            BusinessError: 当物流服务不存在或状态不正确时
        """
        service = ShipmentLogisticsServiceService.get_service_by_id(service_id)
        if not service:
            raise BusinessError('物流服务不存在', code=404)
        
        if service.status != ServiceStatus.PENDING.value:
            raise BusinessError('只能确认待确认状态的服务', code=400)
        
        service.status = ServiceStatus.CONFIRMED.value
        service.confirmed_at = datetime.now()
        
        db.session.commit()
        db.session.refresh(service)
        
        return service
    
    @staticmethod
    def mark_as_reconciled(service_id: int) -> ShipmentLogisticsService:
        """
        标记为已对账
        
        Args:
            service_id: 物流服务ID
            
        Returns:
            更新后的物流服务对象
            
        Raises:
            BusinessError: 当物流服务不存在或状态不正确时
        """
        service = ShipmentLogisticsServiceService.get_service_by_id(service_id)
        if not service:
            raise BusinessError('物流服务不存在', code=404)
        
        if service.status != ServiceStatus.CONFIRMED.value:
            raise BusinessError('只能对账已确认状态的服务', code=400)
        
        service.status = ServiceStatus.RECONCILED.value
        service.reconciled_at = datetime.now()
        
        db.session.commit()
        db.session.refresh(service)
        
        return service
    
    @staticmethod
    def mark_as_paid(service_id: int) -> ShipmentLogisticsService:
        """
        标记为已付款
        
        Args:
            service_id: 物流服务ID
            
        Returns:
            更新后的物流服务对象
            
        Raises:
            BusinessError: 当物流服务不存在或状态不正确时
        """
        service = ShipmentLogisticsServiceService.get_service_by_id(service_id)
        if not service:
            raise BusinessError('物流服务不存在', code=404)
        
        if service.status != ServiceStatus.RECONCILED.value:
            raise BusinessError('只能标记已对账状态的服务为已付款', code=400)
        
        service.status = ServiceStatus.PAID.value
        service.paid_at = datetime.now()
        
        db.session.commit()
        db.session.refresh(service)
        
        return service

