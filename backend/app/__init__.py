import os
import time
from apiflask import APIFlask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask import g, request
from .extensions import db
from .api import register_blueprints
from .logging_config import configure_logging
from .celery_utils import celery_init_app
from .config import config
from app.schemas.base import BaseResponseSchema

def create_app(config_name=None, test_config=None):
    app = APIFlask(__name__, title='IS Vue Admin API', version='1.0.0')
    
    # 0. Configure Logging (Early as possible)
    configure_logging(app)
    
    # 1. Config
    if test_config:
        app.config.update(test_config)
    else:
        # Determine config from env or arg
        if not config_name:
            config_name = os.getenv('FLASK_ENV', 'development')
        
        app.config.from_object(config[config_name])

    # 1.1 Base Response Configuration
    app.config['BASE_RESPONSE_SCHEMA'] = BaseResponseSchema
    app.config['BASE_RESPONSE_DATA_KEY'] = 'data'

    # 1.2 Unified Error Processor
    @app.error_processor
    def custom_error_processor(error):
        # error is an instance of apiflask.exceptions.HTTPError
        
        # Default values
        business_code = 10500 if error.status_code == 500 else 10400 + (error.status_code % 1000)
        data = error.detail
        
        # Extract from extra_data if available (set by BusinessError)
        extra_data = getattr(error, 'extra_data', {})
        if extra_data:
            if 'code' in extra_data:
                business_code = extra_data['code']
            if 'data' in extra_data:
                data = extra_data['data']
        
        # Specific mappings for standard HTTP errors if not overridden
        if not extra_data:
            if error.status_code == 404:
                business_code = 10404
            elif error.status_code == 401:
                business_code = 20101
            elif error.status_code == 403:
                business_code = 20403
            elif error.status_code == 422:
                business_code = 10400 # Bad Request / Validation Error
                # For 422, detail is usually a dict of validation errors
        
        return {
            'code': business_code,
            'message': error.message,
            'data': data
        }, error.status_code, error.headers
    
    # 2. Extensions
    CORS(app, supports_credentials=True)
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
    celery_init_app(app)
    
    # 3. Blueprints
    register_blueprints(app)
    
    # 3.1 Request Logging Hook
    @app.after_request
    def log_request(response):
        if request.path == '/favicon.ico':
            return response
            
        now = time.time()
        duration = round(now - g.start_time, 4) if hasattr(g, 'start_time') else 0
        
        log_data = {
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration': duration,
            'ip': request.remote_addr,
        }
        
        # Try to get user identity if available
        try:
            from flask_jwt_extended import get_jwt_identity
            user_id = get_jwt_identity()
            if user_id:
                log_data['user_id'] = user_id
        except Exception:
            pass
            
        app.logger.info(f"{request.method} {request.path} {response.status_code} {duration}s", extra=log_data)
        return response

    @app.before_request
    def start_timer():
        g.start_time = time.time()
    
    # 4. Models
    with app.app_context():
        from app import models
    
    # 5. CLI Commands
    from app.commands import register_commands
    register_commands(app)

    @app.get('/')
    def index():
        return {
            'data': {
                'message': 'Hello from APIFlask backend!', 
                'version': '1.0.0'
            }
        }
        
    return app
