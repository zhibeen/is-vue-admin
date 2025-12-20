import logging
import logging.config
import os
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """JSON 格式化器，用于结构化日志输出"""
    def format(self, record):
        log_record = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'message': record.getMessage(),
            'logger': record.name,
            'environment': os.getenv('FLASK_ENV', 'development')
        }
        
        # Add extra fields if available (e.g. user_id, request_id)
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'ip_address'):
            log_record['ip_address'] = record.ip_address
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_record, ensure_ascii=False)


class AliyunSLSHandler(logging.Handler):
    """
    阿里云日志服务 Handler（预留接口）
    
    使用前需要安装: pip install aliyun-log-python-sdk
    """
    def __init__(self, endpoint, access_key_id, access_key_secret, project, logstore):
        super().__init__()
        self.enabled = False
        
        try:
            from aliyun.log import LogClient
            self.client = LogClient(endpoint, access_key_id, access_key_secret)
            self.project = project
            self.logstore = logstore
            self.enabled = True
        except ImportError:
            print("Warning: aliyun-log-python-sdk not installed. SLS handler disabled.")
        except Exception as e:
            print(f"Warning: Failed to initialize Aliyun SLS Handler: {e}")
    
    def emit(self, record):
        if not self.enabled:
            return
            
        try:
            from aliyun.log import LogItem
            log_item = LogItem()
            log_item.set_time(int(record.created))
            log_item.set_contents([
                ('level', record.levelname),
                ('message', self.format(record)),
                ('module', record.module),
                ('function', record.funcName),
                ('logger', record.name)
            ])
            self.client.put_logs(self.project, self.logstore, [log_item])
        except Exception as e:
            self.handleError(record)


def get_logging_config(app):
    """
    根据环境返回不同的日志配置
    
    环境变量:
    - FLASK_ENV: development / production / staging
    - LOG_LEVEL: DEBUG / INFO / WARNING / ERROR
    - ENABLE_ALIYUN_SLS: true / false
    """
    # Ensure logs directory exists
    log_dir = os.path.join(app.root_path, '..', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 获取环境配置
    env = os.getenv('FLASK_ENV', 'development')
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    enable_sls = os.getenv('ENABLE_ALIYUN_SLS', 'false').lower() == 'true'
    
    # === 基础配置 === #
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            },
            'detailed': {
                'format': '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
            },
            'json': {
                '()': JSONFormatter,
            },
        },
        'handlers': {},
        'root': {
            'level': log_level,
            'handlers': [],
        },
        'loggers': {}
    }
    
    # === 开发环境配置 === #
    if env == 'development':
        # 控制台：详细的彩色输出
        logging_config['handlers']['console'] = {
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
            'level': 'DEBUG',
        }
        
        # 文件：JSON 格式，保留 30 天
        logging_config['handlers']['file'] = {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(log_dir, 'app.log'),
            'when': 'midnight',
            'interval': 1,
            'backupCount': 30,
            'formatter': 'json',
            'level': 'DEBUG',
            'encoding': 'utf-8',
        }
        
        logging_config['root']['handlers'] = ['console', 'file']
        
        # 应用日志：DEBUG 级别
        logging_config['loggers']['app'] = {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False,
        }
        
        # SQL 查询：WARNING（可临时改为 INFO 调试）
        logging_config['loggers']['sqlalchemy.engine'] = {
            'level': os.getenv('SQL_LOG_LEVEL', 'WARNING'),
            'handlers': ['console'],
            'propagate': False,
        }
    
    # === 生产环境配置 === #
    elif env == 'production':
        # 控制台：简洁输出（Docker 日志收集）
        logging_config['handlers']['console'] = {
            'class': 'logging.StreamHandler',
            'formatter': 'json',  # 生产环境使用 JSON 格式
            'level': 'INFO',
        }
        
        # 文件：JSON 格式，保留 90 天
        logging_config['handlers']['file'] = {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(log_dir, 'app.log'),
            'when': 'midnight',
            'interval': 1,
            'backupCount': 90,  # 生产环境保留更久
            'formatter': 'json',
            'level': 'INFO',
            'encoding': 'utf-8',
        }
        
        # 错误日志单独记录
        logging_config['handlers']['error_file'] = {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(log_dir, 'error.log'),
            'when': 'midnight',
            'interval': 1,
            'backupCount': 90,
            'formatter': 'json',
            'level': 'ERROR',
            'encoding': 'utf-8',
        }
        
        logging_config['root']['handlers'] = ['console', 'file', 'error_file']
        
        # 应用日志：INFO 级别
        logging_config['loggers']['app'] = {
            'level': 'INFO',
            'handlers': ['console', 'file', 'error_file'],
            'propagate': False,
        }
        
        # SQL 查询：只记录错误
        logging_config['loggers']['sqlalchemy.engine'] = {
            'level': 'ERROR',
            'handlers': ['console', 'file'],
            'propagate': False,
        }
        
        # 阿里云 SLS（如果启用）
        if enable_sls:
            sls_endpoint = os.getenv('ALIYUN_SLS_ENDPOINT')
            sls_access_key_id = os.getenv('ALIYUN_ACCESS_KEY_ID')
            sls_access_key_secret = os.getenv('ALIYUN_ACCESS_KEY_SECRET')
            sls_project = os.getenv('ALIYUN_SLS_PROJECT')
            sls_logstore = os.getenv('ALIYUN_SLS_LOGSTORE', 'app-logs')
            
            if all([sls_endpoint, sls_access_key_id, sls_access_key_secret, sls_project]):
                logging_config['handlers']['aliyun_sls'] = {
                    '()': AliyunSLSHandler,
                    'endpoint': sls_endpoint,
                    'access_key_id': sls_access_key_id,
                    'access_key_secret': sls_access_key_secret,
                    'project': sls_project,
                    'logstore': sls_logstore,
                    'level': 'INFO',
                    'formatter': 'json',
                }
                logging_config['root']['handlers'].append('aliyun_sls')
                logging_config['loggers']['app']['handlers'].append('aliyun_sls')
    
    # === 测试环境配置 === #
    elif env == 'staging':
        # 类似生产环境，但保留更多调试信息
        logging_config['handlers']['console'] = {
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
            'level': 'INFO',
        }
        
        logging_config['handlers']['file'] = {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(log_dir, 'app.log'),
            'when': 'midnight',
            'interval': 1,
            'backupCount': 60,
            'formatter': 'json',
            'level': 'INFO',
            'encoding': 'utf-8',
        }
        
        logging_config['root']['handlers'] = ['console', 'file']
        
        logging_config['loggers']['app'] = {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False,
        }
        
        logging_config['loggers']['sqlalchemy.engine'] = {
            'level': 'WARNING',
            'handlers': ['console'],
            'propagate': False,
        }
    
    return logging_config


def configure_logging(app):
    """配置日志系统"""
    logging_config = get_logging_config(app)
    logging.config.dictConfig(logging_config)
    
    env = os.getenv('FLASK_ENV', 'development')
    app.logger.info(f'Logging configured successfully for {env} environment')

