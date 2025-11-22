import logging
import logging.config
import os
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'message': record.getMessage(),
            'logger': record.name
        }
        
        # Add extra fields if available (e.g. user_id, request_id)
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def configure_logging(app):
    # Ensure logs directory exists
    log_dir = os.path.join(app.root_path, '..', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            },
            'json': {
                '()': JSONFormatter,
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': 'DEBUG',
            },
            'file': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': os.path.join(log_dir, 'app.log'),
                'when': 'midnight',
                'interval': 1,
                'backupCount': 30, # Keep logs for 30 days
                'formatter': 'json',
                'level': 'INFO',
                'encoding': 'utf-8',
            },
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
        },
        'loggers': {
            'app': {
                'level': 'DEBUG',
                'handlers': ['console', 'file'],
                'propagate': False,
            },
            'sqlalchemy.engine': {
                'level': 'WARNING', # Set to INFO to see SQL queries
                'handlers': ['console'],
                'propagate': False,
            }
        }
    }

    logging.config.dictConfig(logging_config)
    app.logger.info('Logging configured successfully')

