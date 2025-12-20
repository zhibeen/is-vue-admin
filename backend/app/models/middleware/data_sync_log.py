"""
数据同步日志模型
记录系统间的数据同步情况，用于监控和问题追踪
"""
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func, Text, Index, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.extensions import db


class FinDataSyncLog(db.Model):
    """
    数据同步日志表
    
    作用：
    1. 记录每次数据同步的详细情况
    2. 用于监控数据同步成功率和延迟
    3. 用于问题追踪和数据修复
    
    使用场景：
    - 结算系统推送L1数据到数据中台 → 记录日志
    - 数据中台通知退税系统 → 记录日志
    - 定时任务批量同步 → 记录日志
    """
    __tablename__ = "fin_data_sync_logs"
    
    # ========== 基础信息 ========== #
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # ========== 同步信息 ========== #
    sync_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment='同步类型（realtime=实时, batch=批量, retry=重试, manual=手动）'
    )
    sync_direction: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment='同步方向（如：settlement_to_tax, tax_to_settlement）'
    )
    
    # ========== 来源信息 ========== #
    source_system: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment='来源系统（settlement, tax, logistics等）'
    )
    source_table: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment='来源表名（如：scm_delivery_contracts）'
    )
    source_id: Mapped[int] = mapped_column(
        Integer, 
        nullable=False,
        comment='来源记录ID'
    )
    source_reference_no: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment='来源单号（便于人工查找）'
    )
    
    # ========== 目标信息 ========== #
    target_system: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment='目标系统'
    )
    target_table: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment='目标表名（如果适用）'
    )
    target_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment='目标记录ID（同步成功后填写）'
    )
    target_endpoint: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment='目标API端点（如：/api/v1/tax/webhooks/l1-synced）'
    )
    
    # ========== 同步内容 ========== #
    sync_data: Mapped[dict] = mapped_column(
        JSONB, 
        nullable=False,
        comment='同步数据快照（JSON格式）'
    )
    sync_data_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment='数据大小（字节）'
    )
    
    # ========== 状态与结果 ========== #
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment='状态（pending=待同步, processing=处理中, success=成功, failed=失败, skipped=跳过）'
    )
    
    # ========== 失败处理 ========== #
    error_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment='错误代码（如：NETWORK_ERROR, TIMEOUT, VALIDATION_ERROR）'
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        comment='错误信息（详细错误描述）'
    )
    error_stack_trace: Mapped[Optional[str]] = mapped_column(
        Text,
        comment='错误堆栈（用于开发调试）'
    )
    
    # ========== 重试机制 ========== #
    retry_count: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment='已重试次数'
    )
    max_retry_count: Mapped[int] = mapped_column(
        Integer,
        default=3,
        comment='最大重试次数'
    )
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment='下次重试时间（指数退避）'
    )
    
    # ========== 性能指标 ========== #
    sync_duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment='同步耗时（毫秒）'
    )
    
    # ========== 响应信息 ========== #
    response_code: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment='HTTP响应码（如：200, 404, 500）'
    )
    response_body: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment='响应体（用于调试）'
    )
    
    # ========== 业务凭证关联 ========== #
    voucher_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment='关联的业务凭证ID（如果通过凭证池同步）'
    )
    
    # ========== 关联的订阅 ========== #
    subscription_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment='关联的订阅ID（如果是基于订阅的推送）'
    )
    
    # ========== 通知状态 ========== #
    is_notified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment='是否已发送告警通知（对于失败的同步）'
    )
    notified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment='通知时间'
    )
    
    # ========== 时间字段 ========== #
    sync_started_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(),
        comment='同步开始时间'
    )
    sync_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment='同步完成时间'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(),
        comment='记录创建时间'
    )
    
    # ========== 元数据 ========== #
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment='其他元数据（如：触发用户ID、IP地址等）'
    )
    
    # ========== 索引 ========== #
    __table_args__ = (
        # 按来源查询
        Index('idx_source', 'source_system', 'source_id'),
        # 按目标查询
        Index('idx_target', 'target_system', 'target_id'),
        # 按状态查询（查找失败的同步）
        Index('idx_status', 'status'),
        # 按时间范围查询（统计同步成功率）
        Index('idx_time', 'sync_started_at'),
        # 查询需要重试的记录
        Index('idx_retry', 'status', 'retry_count', 'next_retry_at'),
        # 按业务凭证查询
        Index('idx_voucher', 'voucher_id'),
    )
    
    def __repr__(self):
        return f"<FinDataSyncLog({self.source_system} -> {self.target_system}, status={self.status})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'sync_type': self.sync_type,
            'source_system': self.source_system,
            'source_id': self.source_id,
            'target_system': self.target_system,
            'target_id': self.target_id,
            'status': self.status,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'sync_duration_ms': self.sync_duration_ms,
            'sync_started_at': self.sync_started_at.isoformat() if self.sync_started_at else None,
            'sync_completed_at': self.sync_completed_at.isoformat() if self.sync_completed_at else None,
        }
    
    @classmethod
    def create_log(cls, **kwargs):
        """创建同步日志的快捷方法"""
        log = cls(**kwargs)
        db.session.add(log)
        return log
    
    def mark_success(self, target_id=None, duration_ms=None, response_code=200):
        """标记同步成功"""
        self.status = 'success'
        self.target_id = target_id
        self.sync_duration_ms = duration_ms
        self.response_code = response_code
        self.sync_completed_at = datetime.utcnow()
    
    def mark_failed(self, error_code, error_message, response_code=None):
        """标记同步失败"""
        self.status = 'failed'
        self.error_code = error_code
        self.error_message = error_message
        self.response_code = response_code
        self.sync_completed_at = datetime.utcnow()
        
        # 如果还可以重试，计算下次重试时间（指数退避）
        if self.retry_count < self.max_retry_count:
            from datetime import timedelta
            # 1秒, 2秒, 4秒, 8秒...
            delay_seconds = 2 ** self.retry_count
            self.next_retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)

