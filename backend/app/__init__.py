import os
import time
from apiflask import APIFlask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask import g, request
from .extensions import db
from .api import register_blueprints
from .commands import register_commands
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

    # 1.2 Celery Configuration
    app.config.update(
        CELERY={
            'broker_url': app.config.get('REDIS_URL', 'redis://redis:6379/0'),
            'result_backend': app.config.get('REDIS_URL', 'redis://redis:6379/0'),
            'task_ignore_result': True,
        }
    )

    # 1.3 Unified Error Processor
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
        
        # Build response
        response = {
            'code': business_code,
            'message': error.message,
            'data': data
        }
        
        # Remove null data
        if data is None:
            response.pop('data')
        
        return response, error.status_code, error.headers

    # 2. CORS
    CORS(app, supports_credentials=True)

    # 3. Database
    db.init_app(app)
    Migrate(app, db)

    # 4. JWT
    jwt = JWTManager(app)
    from .security import auth
    app.extensions['auth'] = auth

    # 5. Celery
    celery_app = celery_init_app(app)
    app.extensions['celery'] = celery_app

    # 6. Blueprints
    register_blueprints(app)

    # 6.5. Commands
    register_commands(app)

    # 7. Request logging middleware
    @app.before_request
    def before_request():
        g.start_time = time.time()
        if request.method in ['POST', 'PUT', 'PATCH']:
            app.logger.info('Request started', extra={
                'method': request.method,
                'path': request.path,
                'content_type': request.content_type,
                'content_length': request.content_length
            })

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            response.headers['X-Response-Time'] = f'{duration:.3f}s'
            
            if request.method in ['POST', 'PUT', 'PATCH']:
                app.logger.info('Request completed', extra={
                    'method': request.method,
                    'path': request.path,
                    'status': response.status_code,
                    'duration': f'{duration:.3f}s'
                })
        
        return response

    # 8. Health check
    @app.get('/health')
    def health():
        return {'status': 'healthy', 'timestamp': time.time()}

    return app
