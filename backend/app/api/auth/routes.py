from apiflask import APIBlueprint, abort
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from app.extensions import db
from app.models.user import User
from app.schemas.auth import LoginInput, TokenOutput, UserBaseSchema
from app.security import auth

auth_bp = APIBlueprint('auth', __name__, url_prefix='/auth', tag='Authentication')

@auth_bp.post('/login')
@auth_bp.doc(summary='用户登录', description='使用用户名和密码登录，获取 Access Token 和 Refresh Token。')
@auth_bp.input(LoginInput, arg_name='data')
@auth_bp.output(TokenOutput)
def login(data):
    username = data['username']
    password = data['password']
    
    user = db.session.execute(db.select(User).where(User.username == username)).scalar_one_or_none()
    
    if user is None or not user.check_password(password):
        abort(401, 'Bad username or password')
        
    if not user.is_active:
        abort(403, 'Account is disabled')

    # Create tokens
    # Include permissions in the token claims for frontend RBAC/Permission checks
    # Ensure we are working with list of strings
    permissions_list = list(user.permissions) if user.permissions else []
    roles_list = list(user.role_names) if user.role_names else []
    
    additional_claims = {"roles": roles_list, "permissions": permissions_list}
    
    access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return {
        'data': {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'username': user.username,
            'nickname': user.nickname,
            'roles': roles_list,
            'permissions': permissions_list
        }
    }

@auth_bp.get('/me')
@auth_bp.auth_required(auth)
@auth_bp.doc(summary='获取当前用户信息', description='验证 Access Token 并返回当前登录用户的详细信息。')
@auth_bp.output(UserBaseSchema)
def me():
    # auth.current_user is automatically populated by verify_token
    user = auth.current_user
    if not user:
        abort(404, 'User not found')
        
    # Explicitly wrap in data key for BaseResponseSchema
    return {'data': user}

@auth_bp.post('/refresh')
# Refresh Token 也是一种 JWT，但它的用途不同。
# flask-jwt-extended 区分 Access 和 Refresh Token。
# auth.verify_token 默认验证的是 Authorization Header 里的 Access Token。
# 所以 Refresh 接口我们不能用 @auth_bp.auth_required(auth)，而应该用 @jwt_required(refresh=True)
# 为了让文档显示安全要求，我们可以手动指定 security
@auth_bp.doc(security='BearerAuth', summary='刷新 Access Token', description='使用 Refresh Token 获取一个新的 Access Token。')
@jwt_required(refresh=True)
@auth_bp.output(TokenOutput)
def refresh():
    """Get a new access token using refresh token"""
    current_user_id = get_jwt_identity()
    user = db.session.get(User, int(current_user_id))
    if not user:
        abort(404)
        
    # Include permissions in refresh token as well, or just roles?
    # Usually refresh token just gets a new access token.
    # The access token needs roles & permissions.
    
    permissions_list = list(user.permissions) if user.permissions else []
    roles_list = list(user.role_names) if user.role_names else []
    
    new_access_token = create_access_token(
        identity=current_user_id, 
        additional_claims={
            "roles": roles_list,
            "permissions": permissions_list
        }
    )
    # Add nickname to refresh response as well to keep frontend store updated if needed
    return {
        'data': {
            'access_token': new_access_token,
            'nickname': user.nickname,
            'username': user.username, # Also return username for completeness
            'roles': roles_list,
            'permissions': permissions_list
        }
    }

