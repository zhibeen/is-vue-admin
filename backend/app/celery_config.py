"""独立的Celery配置模块，避免循环导入"""
from celery import Celery

def make_celery():
    """创建Celery应用实例"""
    celery = Celery(
        'is_admin',
        broker='redis://redis:6379/0',
        backend='redis://redis:6379/0',
        include=['app.tasks']
    )
    
    # 基础配置
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_ignore_result=True,
    )
    
    return celery

# 创建Celery实例
celery_app = make_celery()
