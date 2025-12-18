"""
报关单审计日志服务
"""
from typing import Dict, Optional, Any
from flask import request, g
from flask_jwt_extended import get_jwt_identity, get_jwt
from app.extensions import db
from app.models.customs.audit_log import CustomsDeclarationAuditLog
import logging

logger = logging.getLogger(__name__)


class AuditService:
    """
    审计日志服务
    记录报关单的所有重要操作
    """
    
    @staticmethod
    def log_action(
        declaration_id: int,
        action: str,
        description: str,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        changes_summary: Optional[str] = None
    ) -> CustomsDeclarationAuditLog:
        """
        记录操作日志
        
        Args:
            declaration_id: 报关单ID
            action: 操作类型
            description: 操作描述
            old_value: 变更前的值
            new_value: 变更后的值
            changes_summary: 变更摘要
            
        Returns:
            审计日志对象
        """
        try:
            # 获取当前用户信息
            operator_id = None
            operator_name = None
            
            try:
                current_user_id = get_jwt_identity()
                if current_user_id:
                    operator_id = current_user_id
                    # 尝试从 JWT claims 获取用户名
                    claims = get_jwt()
                    operator_name = claims.get('username', f'User_{current_user_id}')
            except:
                pass  # 非认证请求
            
            # 获取请求信息
            ip_address = None
            user_agent = None
            
            if request:
                ip_address = request.remote_addr
                user_agent = request.headers.get('User-Agent', '')[:500]
            
            # 创建审计日志
            audit_log = CustomsDeclarationAuditLog(
                declaration_id=declaration_id,
                action=action,
                action_description=description,
                old_value=old_value,
                new_value=new_value,
                changes_summary=changes_summary,
                operator_id=operator_id,
                operator_name=operator_name,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.session.add(audit_log)
            db.session.commit()
            
            # 记录到应用日志
            logger.info(
                f"Audit: {action} on declaration {declaration_id} by {operator_name}",
                extra={
                    'declaration_id': declaration_id,
                    'action': action,
                    'operator_id': operator_id
                }
            )
            
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # 审计日志失败不应阻断主流程
            db.session.rollback()
            return None
    
    @staticmethod
    def log_create(declaration_id: int, data: Dict) -> None:
        """记录创建操作"""
        AuditService.log_action(
            declaration_id=declaration_id,
            action='create',
            description='创建报关单',
            new_value=data,
            changes_summary=f"创建报关单，预录入编号: {data.get('pre_entry_no', '-')}"
        )
    
    @staticmethod
    def log_update(declaration_id: int, old_data: Dict, new_data: Dict, changes: list) -> None:
        """记录更新操作"""
        summary = f"更新了 {len(changes)} 个字段: {', '.join(changes[:5])}"
        if len(changes) > 5:
            summary += f"等 {len(changes)} 个字段"
        
        AuditService.log_action(
            declaration_id=declaration_id,
            action='update',
            description='更新报关单数据',
            old_value=old_data,
            new_value=new_data,
            changes_summary=summary
        )
    
    @staticmethod
    def log_status_change(
        declaration_id: int,
        old_status: str,
        new_status: str,
        reason: Optional[str] = None
    ) -> None:
        """记录状态变更"""
        summary = f"状态从 '{old_status}' 变更为 '{new_status}'"
        if reason:
            summary += f"，原因: {reason}"
        
        AuditService.log_action(
            declaration_id=declaration_id,
            action='status_change',
            description='变更报关单状态',
            old_value={'status': old_status},
            new_value={'status': new_status, 'reason': reason},
            changes_summary=summary
        )
    
    @staticmethod
    def log_file_upload(declaration_id: int, filename: str, file_category: str) -> None:
        """记录文件上传"""
        AuditService.log_action(
            declaration_id=declaration_id,
            action='file_upload',
            description='上传附件',
            new_value={'filename': filename, 'category': file_category},
            changes_summary=f"上传文件: {filename} ({file_category})"
        )
    
    @staticmethod
    def log_delete(declaration_id: int, data: Dict) -> None:
        """记录删除操作"""
        AuditService.log_action(
            declaration_id=declaration_id,
            action='delete',
            description='删除报关单',
            old_value=data,
            changes_summary=f"删除报关单 {data.get('entry_no', declaration_id)}"
        )
    
    @staticmethod
    def get_logs(declaration_id: int, limit: int = 50) -> list:
        """
        获取报关单的审计日志
        
        Args:
            declaration_id: 报关单ID
            limit: 返回记录数限制
            
        Returns:
            审计日志列表
        """
        return db.session.query(CustomsDeclarationAuditLog)\
            .filter_by(declaration_id=declaration_id)\
            .order_by(CustomsDeclarationAuditLog.created_at.desc())\
            .limit(limit)\
            .all()


# 创建全局实例
audit_service = AuditService()

