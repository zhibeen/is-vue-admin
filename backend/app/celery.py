from celery import Celery
from app import create_app

def make_celery(app=None):
    """创建Celery应用"""
    app = app or create_app()
    
    celery = Celery(
        app.import_name,
        broker=app.config.get('CELERY_BROKER_URL', 'redis://redis:6379/0'),
        backend=app.config.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
        include=['app.tasks']
    )
    
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# 创建Celery实例
celery = make_celery()
