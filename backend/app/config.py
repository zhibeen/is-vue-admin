import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Celery Defaults
    CELERY = dict(
        broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        task_ignore_result=True,
    )

    # === Synology NAS Base Config ===
    # 基础配置，具体 root_dir 会在各环境子类中重写
    NAS_CONFIG = {
        'host': os.getenv('SYNOLOGY_NAS_HOST', 'http://192.168.1.50:5000'),
        'user': os.getenv('SYNOLOGY_NAS_USER', 'admin'),
        'password': os.getenv('SYNOLOGY_NAS_PASSWORD', ''),
        'verify_ssl': os.getenv('SYNOLOGY_NAS_VERIFY_SSL', 'False').lower() in ('true', '1', 't'),
        'timeout': int(os.getenv('SYNOLOGY_NAS_TIMEOUT', 30)),
        'root_dir': '/serc_files/default' # 默认值，防报错
    }
    
    # === 领星ERP API配置 ===
    LINGXING_API_BASE_URL = os.getenv('LINGXING_API_BASE_URL', 'https://api.lingxing.com')
    LINGXING_APP_KEY = os.getenv('LINGXING_APP_KEY', '')
    LINGXING_APP_SECRET = os.getenv('LINGXING_APP_SECRET', '')
    LINGXING_TIMEOUT = int(os.getenv('LINGXING_TIMEOUT', '30'))
    LINGXING_MAX_RETRIES = int(os.getenv('LINGXING_MAX_RETRIES', '3'))

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # 开发环境：使用 /serc_files/dev 目录
    # 注意：需使用 copy() 避免修改基类引用
    NAS_CONFIG = Config.NAS_CONFIG.copy()
    NAS_CONFIG['root_dir'] = os.getenv('SYNOLOGY_NAS_BASE_DIR', '/serc_files') + '/dev'

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # 生产环境：使用 /serc_files/prod 目录
    NAS_CONFIG = Config.NAS_CONFIG.copy()
    NAS_CONFIG['root_dir'] = os.getenv('SYNOLOGY_NAS_BASE_DIR', '/serc_files') + '/prod'
    # In production, ensure strong secrets are loaded
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_SECRET_KEY = 'test-secret'
    SECRET_KEY = 'test-secret'

    # 测试环境：使用 /serc_files/test 目录
    NAS_CONFIG = Config.NAS_CONFIG.copy()
    NAS_CONFIG['root_dir'] = os.getenv('SYNOLOGY_NAS_BASE_DIR', '/serc_files') + '/test'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
