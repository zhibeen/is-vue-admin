"""
数据订阅模型
管理系统间的数据订阅关系
"""
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func, Text, Boolean, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.extensions import db


class DataSubscription(db.Model):
    """
    数据订阅表
    
    作用：
    1. 管理系统间的订阅关系（谁订阅了什么数据）
    2. 配置推送规则（推送到哪里、推送什么）
    3. 控制数据流向
    
    使用场景：
    - 退税系统订阅L1交付合同的变更
    - 财务系统订阅付款完成事件
    - 成本系统订阅物流成本数据
    """
    __tablename__ = "data_subscriptions"
    
    # ========== 基础信息 ========== #
    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment='订阅名称（如：退税系统订阅L1数据）'
    )
    
    # ========== 订阅方信息 ========== #
    subscriber_system: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment='订阅方系统（tax, finance, cost等）'
    )
    subscriber_module: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment='订阅方模块（可选，用于更细粒度的控制）'
    )
    
    # ========== 订阅内容 ========== #
    event_types: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        comment='订阅的事件类型列表（如：["l1_confirmed", "invoice_created"]）'
    )
    source_systems: Mapped[Optional[list]] = mapped_column(
        JSONB,
        comment='来源系统过滤（如果只订阅特定系统的数据）'
    )
    
    # ========== 推送配置 ========== #
    webhook_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment='Webhook推送地址'
    )
    webhook_method: Mapped[str] = mapped_column(
        String(10),
        default='POST',
        comment='HTTP方法（POST/PUT）'
    )
    webhook_headers: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment='自定义HTTP头（如：{"Authorization": "Bearer xxx"}）'
    )
    
    # ========== 数据过滤 ========== #
    filters: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment='数据过滤条件（JSON格式，如：{"company_id": [1,2,3]}）'
    )
    include_fields: Mapped[Optional[list]] = mapped_column(
        JSONB,
        comment='包含字段列表（为空表示全部字段）'
    )
    exclude_fields: Mapped[Optional[list]] = mapped_column(
        JSONB,
        comment='排除字段列表（敏感字段可以排除）'
    )
    
    # ========== 推送策略 ========== #
    push_mode: Mapped[str] = mapped_column(
        String(20),
        default='realtime',
        comment='推送模式（realtime=实时, batch=批量, scheduled=定时）'
    )
    batch_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment='批量推送时的批次大小'
    )
    batch_interval_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment='批量推送时的时间间隔（秒）'
    )
    schedule_cron: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment='定时推送的cron表达式（如：0 2 * * *）'
    )
    
    # ========== 重试配置 ========== #
    retry_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment='是否启用重试'
    )
    max_retry_count: Mapped[int] = mapped_column(
        Integer,
        default=3,
        comment='最大重试次数'
    )
    retry_strategy: Mapped[str] = mapped_column(
        String(20),
        default='exponential',
        comment='重试策略（exponential=指数退避, fixed=固定间隔）'
    )
    
    # ========== 状态管理 ========== #
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment='是否激活（可以暂停订阅）'
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default='normal',
        comment='状态（normal=正常, error=异常, suspended=暂停）'
    )
    
    # ========== 监控统计 ========== #
    total_pushed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment='累计推送次数'
    )
    success_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment='成功次数'
    )
    failed_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment='失败次数'
    )
    last_push_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment='最后推送时间'
    )
    last_success_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment='最后成功时间'
    )
    last_error: Mapped[Optional[str]] = mapped_column(
        Text,
        comment='最后一次错误信息'
    )
    
    # ========== 告警配置 ========== #
    alert_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment='是否启用告警'
    )
    alert_threshold: Mapped[int] = mapped_column(
        Integer,
        default=10,
        comment='连续失败次数超过此值时告警'
    )
    alert_contacts: Mapped[Optional[list]] = mapped_column(
        JSONB,
        comment='告警联系人（邮箱/手机号）'
    )
    
    # ========== 审计字段 ========== #
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment='创建时间'
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        onupdate=func.now(),
        comment='更新时间'
    )
    created_by: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='创建人ID'
    )
    
    # ========== 备注 ========== #
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment='订阅说明'
    )
    
    # ========== 索引 ========== #
    __table_args__ = (
        # 按订阅方查询
        Index('idx_subscriber', 'subscriber_system'),
        # 按状态查询
        Index('idx_status', 'is_active', 'status'),
        # 查询需要推送的订阅
        Index('idx_push_mode', 'push_mode', 'is_active'),
    )
    
    def __repr__(self):
        return f"<DataSubscription({self.subscription_name}, active={self.is_active})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'subscription_name': self.subscription_name,
            'subscriber_system': self.subscriber_system,
            'event_types': self.event_types,
            'webhook_url': self.webhook_url,
            'push_mode': self.push_mode,
            'is_active': self.is_active,
            'status': self.status,
            'total_pushed': self.total_pushed,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'last_push_at': self.last_push_at.isoformat() if self.last_push_at else None,
        }
    
    def should_push(self, event_type, source_system=None):
        """判断是否应该推送此事件"""
        if not self.is_active:
            return False
        
        # 检查事件类型
        if event_type not in self.event_types:
            return False
        
        # 检查来源系统过滤
        if self.source_systems and source_system:
            if source_system not in self.source_systems:
                return False
        
        return True
    
    def record_push_result(self, success=True, error_message=None):
        """记录推送结果"""
        self.total_pushed += 1
        self.last_push_at = datetime.utcnow()
        
        if success:
            self.success_count += 1
            self.last_success_at = datetime.utcnow()
            self.status = 'normal'
        else:
            self.failed_count += 1
            self.last_error = error_message
            
            # 检查是否需要告警
            if self.alert_enabled and self.failed_count >= self.alert_threshold:
                self.status = 'error'
                # TODO: 发送告警通知

