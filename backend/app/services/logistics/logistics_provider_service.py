"""
物流服务商服务层
处理物流服务商的CRUD业务逻辑
"""
from typing import List, Optional
from sqlalchemy import select
from app.models.logistics.logistics_provider import LogisticsProvider
from app.extensions import db
from app.errors import BusinessError


class LogisticsProviderService:
    """物流服务商业务逻辑类"""
    
    @staticmethod
    def create_provider(data: dict) -> LogisticsProvider:
        """
        创建物流服务商
        
        Args:
            data: 服务商数据
            
        Returns:
            创建的服务商对象
            
        Raises:
            BusinessError: 当服务商编码已存在时
        """
        # 检查编码是否重复
        existing = db.session.execute(
            select(LogisticsProvider).where(
                LogisticsProvider.provider_code == data['provider_code']
            )
        ).scalar_one_or_none()
        
        if existing:
            raise BusinessError('服务商编码已存在', code=400)
        
        # 创建服务商
        provider = LogisticsProvider(**data)
        db.session.add(provider)
        db.session.commit()
        db.session.refresh(provider)
        
        return provider
    
    @staticmethod
    def get_provider_by_id(provider_id: int) -> Optional[LogisticsProvider]:
        """
        根据ID获取服务商
        
        Args:
            provider_id: 服务商ID
            
        Returns:
            服务商对象或None
        """
        return db.session.get(LogisticsProvider, provider_id)
    
    @staticmethod
    def get_provider_by_code(provider_code: str) -> Optional[LogisticsProvider]:
        """
        根据编码获取服务商
        
        Args:
            provider_code: 服务商编码
            
        Returns:
            服务商对象或None
        """
        return db.session.execute(
            select(LogisticsProvider).where(
                LogisticsProvider.provider_code == provider_code
            )
        ).scalar_one_or_none()
    
    @staticmethod
    def get_all_providers(
        is_active: Optional[bool] = None,
        service_type: Optional[str] = None
    ) -> List[LogisticsProvider]:
        """
        获取所有服务商列表（支持筛选）
        
        Args:
            is_active: 是否启用（None表示不筛选）
            service_type: 服务类型（None表示不筛选）
            
        Returns:
            服务商列表
        """
        stmt = select(LogisticsProvider)
        
        # 筛选条件
        if is_active is not None:
            stmt = stmt.where(LogisticsProvider.is_active == is_active)
        if service_type:
            stmt = stmt.where(LogisticsProvider.service_type == service_type)
        
        # 排序
        stmt = stmt.order_by(LogisticsProvider.provider_name)
        
        return db.session.execute(stmt).scalars().all()
    
    @staticmethod
    def update_provider(provider_id: int, data: dict) -> LogisticsProvider:
        """
        更新服务商信息
        
        Args:
            provider_id: 服务商ID
            data: 更新数据
            
        Returns:
            更新后的服务商对象
            
        Raises:
            BusinessError: 当服务商不存在时
        """
        provider = LogisticsProviderService.get_provider_by_id(provider_id)
        if not provider:
            raise BusinessError('服务商不存在', code=404)
        
        # 更新字段
        for key, value in data.items():
            if hasattr(provider, key):
                setattr(provider, key, value)
        
        db.session.commit()
        db.session.refresh(provider)
        
        return provider
    
    @staticmethod
    def delete_provider(provider_id: int) -> None:
        """
        删除服务商
        
        Args:
            provider_id: 服务商ID
            
        Raises:
            BusinessError: 当服务商不存在或已被使用时
        """
        provider = LogisticsProviderService.get_provider_by_id(provider_id)
        if not provider:
            raise BusinessError('服务商不存在', code=404)
        
        # TODO: 检查是否有关联的物流服务记录，如果有则不允许删除
        # 这部分逻辑在阶段2实现
        
        db.session.delete(provider)
        db.session.commit()
    
    @staticmethod
    def toggle_active_status(provider_id: int) -> LogisticsProvider:
        """
        切换服务商启用状态
        
        Args:
            provider_id: 服务商ID
            
        Returns:
            更新后的服务商对象
            
        Raises:
            BusinessError: 当服务商不存在时
        """
        provider = LogisticsProviderService.get_provider_by_id(provider_id)
        if not provider:
            raise BusinessError('服务商不存在', code=404)
        
        provider.is_active = not provider.is_active
        db.session.commit()
        db.session.refresh(provider)
        
        return provider

