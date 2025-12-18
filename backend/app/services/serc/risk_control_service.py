from decimal import Decimal
from typing import Dict, Optional, Any
from app.extensions import db
from app.models.serc.tax import SysExchangeRate
from app.models.serc.foundation import SysHSCode

class RiskControlService:
    def check_exchange_rate_risk(self, declaration_fob_usd: Decimal, procurement_cost_cny: Decimal, currency: str = 'USD') -> Dict[str, Any]:
        """
        计算换汇成本并进行风控
        换汇成本 = 采购成本(CNY) / 出口FOB(USD)
        """
        # 1. 基础校验
        if declaration_fob_usd <= 0:
             return {
                 "is_blocked": True, 
                 "reason": "出口申报金额(FOB)必须大于0", 
                 "cost": 0
             }
             
        # 2. 计算换汇成本
        exchange_cost = procurement_cost_cny / declaration_fob_usd
        
        # 3. 获取配置
        config = db.session.query(SysExchangeRate).filter_by(currency=currency, is_active=True).first()
        
        # 默认安全区间 (如果未配置)
        safe_min = config.safe_min if config else Decimal('5.0')
        safe_max = config.safe_max if config else Decimal('8.0')
        
        is_blocked = False
        warning = None
        
        # 4. 判定
        if exchange_cost < safe_min:
            warning = f"换汇成本 {exchange_cost:.2f} 低于安全下限 {safe_min}，存在低报采购价或高报出口价风险"
            # 低换汇成本通常不阻断，只警告 (可能利润极高)
            
        if exchange_cost > safe_max:
             is_blocked = True
             warning = f"换汇成本 {exchange_cost:.2f} 超出安全上限 {safe_max}，存在亏损出口或虚假贸易风险"
             
        return {
            "is_blocked": is_blocked,
            "reason": warning,
            "cost": float(exchange_cost),
            "safe_range": [float(safe_min), float(safe_max)]
        }

risk_control_service = RiskControlService()

