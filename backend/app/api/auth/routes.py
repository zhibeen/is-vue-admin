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
    permissions = list(user.permissions)
    additional_claims = {"roles": user.role_names, "permissions": permissions}
    
    access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'username': user.username,
        'roles': user.role_names,
        'permissions': permissions
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
        
    # user.role_names and user.permissions are handled by Schema attributes
    return user

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
        
    new_access_token = create_access_token(identity=current_user_id, additional_claims={"roles": user.role_names})
    return {'access_token': new_access_token}

