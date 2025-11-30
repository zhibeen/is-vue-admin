import time
import random
from datetime import datetime
from flask import current_app
# 尝试导入 Redis，如果未安装则回退
try:
    from redis import Redis
except ImportError:
    Redis = None

def get_redis_client():
    """获取 Redis 客户端 (懒加载)"""
    # 假设使用 Flask-Redis 或直接从 config 获取 URL
    # 这里简化处理，尝试从 current_app extensions 获取，或者创建新的
    if hasattr(current_app, 'extensions') and 'redis' in current_app.extensions:
        return current_app.extensions['redis']
    
    # Fallback: Create standard client if REDIS_URL exists
    redis_url = current_app.config.get('REDIS_URL') or 'redis://redis:6379/0'
    if Redis:
        return Redis.from_url(redis_url, decode_responses=True)
    return None

def generate_seq_no(prefix: str, company_code: str = None) -> str:
    """
    生成唯一业务单号
    格式: {COMPANY_CODE}-{PREFIX}-{YYMM}-{SEQ}
    Example: SZ-L1-2311-0001
    
    如果 company_code 为空，则省略前缀部分。
    """
    now = datetime.now()
    yymm = now.strftime("%y%m") # 2311
    
    # 构造 Sequence Key: seq:L1:SZ:2311 (按公司按月隔离)
    # 如果没有公司代码，则全局共享: seq:L1:GLOBAL:2311
    comp_key = company_code if company_code else "GLOBAL"
    seq_key = f"seq:{prefix}:{comp_key}:{yymm}"
    
    redis_client = get_redis_client()
    
    if redis_client:
        try:
            # Redis Incr (Atomic)
            seq_num = redis_client.incr(seq_key)
            # 设置过期时间 (比如 2 个月后过期，节省空间，只要保证当月不过期即可)
            if seq_num == 1:
                redis_client.expire(seq_key, 60 * 60 * 24 * 60)
        except Exception as e:
            # Redis 失败降级
            current_app.logger.error(f"Redis sequence generation failed: {e}")
            seq_num = random.randint(1000, 9999) 
    else:
        # 无 Redis 时的降级策略 (开发环境)
        # 使用微秒级时间戳模拟递增，或者随机数
        # 注意：这种方式在高并发下无法保证连续且唯一
        seq_num = random.randint(1, 9999)

    # 格式化流水号 (4位，不足补0)
    seq_str = f"{seq_num:04d}"
    
    parts = []
    if company_code:
        parts.append(company_code)
    
    parts.append(prefix)
    parts.append(yymm)
    parts.append(seq_str)
    
    return "-".join(parts)
