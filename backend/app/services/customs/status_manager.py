"""
报关单状态流转管理
"""
from typing import Dict, List, Optional
from app.models.serc.enums import CustomsStatus
from app.errors import BusinessError


class DeclarationStatusManager:
    """
    报关单状态流转管理器
    定义状态转换规则和业务逻辑
    """
    
    # 状态转换规则：当前状态 -> [允许转换的目标状态]
    ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
        CustomsStatus.DRAFT.value: [
            CustomsStatus.PENDING_REVIEW.value,  # 提交审核
        ],
        CustomsStatus.PENDING_REVIEW.value: [
            CustomsStatus.DECLARED.value,  # 审核通过，申报
            CustomsStatus.DRAFT.value,     # 审核退回
        ],
        CustomsStatus.DECLARED.value: [
            CustomsStatus.CLEARED.value,   # 海关放行
            CustomsStatus.AMENDING.value,  # 申请修撤
        ],
        CustomsStatus.CLEARED.value: [
            CustomsStatus.ARCHIVED.value,  # 归档
        ],
        CustomsStatus.AMENDING.value: [
            CustomsStatus.AMENDMENT_APPROVED.value,  # 修改批准
            CustomsStatus.DECLARED.value,            # 拒绝修改，恢复
        ],
        CustomsStatus.AMENDMENT_APPROVED.value: [
            CustomsStatus.PENDING_REVIEW.value,  # 重新走审批流程
        ],
        CustomsStatus.ARCHIVED.value: [],  # 归档后不可再转换
    }
    
    # 锁定状态：这些状态下数据不可编辑
    LOCKED_STATUSES = [
        CustomsStatus.PENDING_REVIEW.value,
        CustomsStatus.DECLARED.value,
        CustomsStatus.CLEARED.value,
        CustomsStatus.ARCHIVED.value,
    ]
    
    # 状态描述
    STATUS_DESCRIPTIONS = {
        CustomsStatus.DRAFT.value: "草稿 - 可自由编辑",
        CustomsStatus.PENDING_REVIEW.value: "待审核 - 已锁定",
        CustomsStatus.DECLARED.value: "已申报 - 等待海关结果",
        CustomsStatus.CLEARED.value: "已放行 - 可生成交付合同",
        CustomsStatus.AMENDING.value: "修撤中 - 修改申请已提交",
        CustomsStatus.AMENDMENT_APPROVED.value: "修改已批准 - 需重新走流程",
        CustomsStatus.ARCHIVED.value: "已归档 - 不可修改",
    }
    
    # 状态转换操作描述（更友好的前端提示）
    TRANSITION_ACTIONS = {
        (CustomsStatus.DRAFT.value, CustomsStatus.PENDING_REVIEW.value): "提交审核",
        (CustomsStatus.PENDING_REVIEW.value, CustomsStatus.DECLARED.value): "审核通过并申报",
        (CustomsStatus.PENDING_REVIEW.value, CustomsStatus.DRAFT.value): "审核退回",
        (CustomsStatus.DECLARED.value, CustomsStatus.CLEARED.value): "确认放行",
        (CustomsStatus.DECLARED.value, CustomsStatus.AMENDING.value): "申请修撤",
        (CustomsStatus.CLEARED.value, CustomsStatus.ARCHIVED.value): "归档",
        (CustomsStatus.AMENDING.value, CustomsStatus.AMENDMENT_APPROVED.value): "批准修撤",
        (CustomsStatus.AMENDING.value, CustomsStatus.DECLARED.value): "拒绝修撤",
        (CustomsStatus.AMENDMENT_APPROVED.value, CustomsStatus.PENDING_REVIEW.value): "重新提交审核",
    }
    
    @classmethod
    def can_transition(cls, current_status: str, target_status: str) -> bool:
        """
        检查是否允许状态转换
        
        Args:
            current_status: 当前状态
            target_status: 目标状态
            
        Returns:
            是否允许转换
        """
        allowed = cls.ALLOWED_TRANSITIONS.get(current_status, [])
        return target_status in allowed
    
    @classmethod
    def validate_transition(cls, current_status: str, target_status: str) -> None:
        """
        验证状态转换，不允许则抛出异常
        
        Args:
            current_status: 当前状态
            target_status: 目标状态
            
        Raises:
            BusinessError: 不允许的状态转换
        """
        if not cls.can_transition(current_status, target_status):
            current_desc = cls.STATUS_DESCRIPTIONS.get(current_status, current_status)
            target_desc = cls.STATUS_DESCRIPTIONS.get(target_status, target_status)
            raise BusinessError(
                f"不允许从 '{current_desc}' 转换到 '{target_desc}'",
                code=400
            )
    
    @classmethod
    def is_locked(cls, status: str) -> bool:
        """
        检查指定状态是否锁定（不可编辑）
        
        Args:
            status: 状态
            
        Returns:
            是否锁定
        """
        return status in cls.LOCKED_STATUSES
    
    @classmethod
    def get_allowed_transitions(cls, current_status: str) -> List[Dict[str, str]]:
        """
        获取当前状态允许的转换列表
        
        Args:
            current_status: 当前状态
            
        Returns:
            允许的转换列表，包含状态码和描述
        """
        allowed = cls.ALLOWED_TRANSITIONS.get(current_status, [])
        return [
            {
                'status': status,
                'description': cls.TRANSITION_ACTIONS.get(
                    (current_status, status),
                    cls.STATUS_DESCRIPTIONS.get(status, status)
                )
            }
            for status in allowed
        ]
    
    @classmethod
    def get_status_flow(cls) -> Dict[str, List[str]]:
        """
        获取完整的状态流转图
        
        Returns:
            状态流转图
        """
        return cls.ALLOWED_TRANSITIONS.copy()


# 状态转换的业务规则检查器
class StatusTransitionValidator:
    """
    状态转换的业务规则验证器
    """
    
    @staticmethod
    def validate_submit_for_review(declaration) -> None:
        """
        验证提交审核的前置条件
        
        Args:
            declaration: 报关单对象
            
        Raises:
            BusinessError: 不满足提交条件
        """
        errors = []
        
        # 1. 必须有境内发货人
        if not declaration.internal_shipper_id:
            errors.append("未指定境内发货人")
        
        # 2. 必须有商品明细
        if not declaration.items or len(declaration.items) == 0:
            errors.append("没有商品明细")
        
        # 3. 必须有出口日期
        if not declaration.export_date:
            errors.append("未填写出口日期")
        
        # 4. 商品明细必须有HS编码
        for idx, item in enumerate(declaration.items, 1):
            if not item.hs_code:
                errors.append(f"第 {idx} 行商品缺少 HS 编码")
        
        if errors:
            raise BusinessError(
                f"提交审核失败：{'; '.join(errors)}",
                code=400
            )
    
    @staticmethod
    def validate_declare(declaration) -> None:
        """
        验证申报的前置条件
        
        Args:
            declaration: 报关单对象
            
        Raises:
            BusinessError: 不满足申报条件
        """
        errors = []
        
        # 申报时所有核心字段必须完整
        required_fields = {
            'entry_port': '申报口岸',
            'destination_country': '运抵国',
            'trade_mode': '监管方式',
            'transaction_mode': '成交方式',
        }
        
        for field, label in required_fields.items():
            if not getattr(declaration, field, None):
                errors.append(f"未填写{label}")
        
        if errors:
            raise BusinessError(
                f"申报失败：{'; '.join(errors)}",
                code=400
            )
    
    @staticmethod
    def validate_cleared(declaration) -> None:
        """
        验证放行的前置条件
        
        Args:
            declaration: 报关单对象
            
        Raises:
            BusinessError: 不满足放行条件
        """
        errors = []
        
        # 1. 必须已申报
        if declaration.status != CustomsStatus.DECLARED.value:
            errors.append("只有已申报的报关单才能放行")
        
        # 2. 必须有报关单单号（海关编号）
        if not declaration.customs_no:
            errors.append("缺少报关单单号（海关编号）")
        
        if errors:
            raise BusinessError(
                f"放行失败：{'; '.join(errors)}",
                code=400
            )
    
    @staticmethod
    def validate_archive(declaration) -> None:
        """
        验证归档的前置条件
        
        Args:
            declaration: 报关单对象
            
        Raises:
            BusinessError: 不满足归档条件
        """
        from app.models.customs.attachment import CustomsAttachment
        from app.extensions import db
        
        errors = []
        
        # 1. 必须已放行
        if declaration.status != CustomsStatus.CLEARED.value:
            errors.append("只有已放行的报关单才能归档")
        
        # 2. 检查必要文件是否已上传（使用动态的 required_file_slots）
        required_files = declaration.required_file_slots  # 动态获取必需文件列表（根据整柜/散货自动调整）
        
        # 查询已上传的文件插槽
        uploaded_slots = db.session.query(CustomsAttachment.slot_title).filter(
            CustomsAttachment.declaration_id == declaration.id,
            CustomsAttachment.slot_title.isnot(None)  # 确保有槽位标题
        ).distinct().all()
        
        uploaded_slot_names = {slot[0] for slot in uploaded_slots if slot[0]}
        
        # 检查缺失的必要文件
        missing_files = [f for f in required_files if f not in uploaded_slot_names]
        
        if missing_files:
            errors.append(f"资料不齐全，缺少以下文件：{', '.join(missing_files)}")
        
        # 3. 必须有FOB总价
        if not declaration.fob_total or declaration.fob_total <= 0:
            errors.append("FOB总价必须大于0")
        
        # 4. 必须有海关编号（已申报并放行）
        if not declaration.customs_no:
            errors.append("缺少海关编号")
        
        if errors:
            raise BusinessError(
                f"归档失败：{'; '.join(errors)}",
                code=400
            )

