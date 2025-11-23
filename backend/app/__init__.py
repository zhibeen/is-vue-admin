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
        return {
            'code': error.status_code,
            'message': error.message,
            'data': error.detail if error.detail else None
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

    @app.get('/')
    def index():
        return {
            'data': {
                'message': 'Hello from APIFlask backend!', 
                'version': '1.0.0'
            }
        }
        
    return app
