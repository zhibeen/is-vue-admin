import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Celery Defaults
    CELERY = dict(
        broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        task_ignore_result=True,
    )

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    # In production, ensure strong secrets are loaded
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_SECRET_KEY = 'test-secret'
    SECRET_KEY = 'test-secret'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

