from apiflask import HTTPTokenAuth
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.extensions import db
from app.models.user import User

# 定义 Bearer Token 认证方案
# 移除 header='Authorization' 参数，让 APIFlask 默认使用 HTTP Bearer 模式
# 这样 Swagger UI 会自动添加 "Bearer " 前缀
auth = HTTPTokenAuth(scheme='Bearer')

@auth.verify_token
def verify_token(token):
    """
    验证 Token。
    """
    try:
        # 委托给 flask-jwt-extended 验证 Token 有效性 (过期、签名等)
        verify_jwt_in_request()
        
        # 获取用户身份
        user_id = get_jwt_identity()
        if not user_id:
            print("DEBUG: No user_id found in token")
            return None
            
        user = db.session.get(User, int(user_id))
        if not user:
            print(f"DEBUG: User {user_id} not found in DB")
            return None
            
        return user
    except Exception as e:
        print(f"DEBUG: Auth Failed: {str(e)}")
        # 验证失败返回 None，APIFlask 会自动处理为 401
        return None

