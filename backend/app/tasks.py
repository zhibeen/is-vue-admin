from celery import shared_task
import time

@shared_task
def send_email_task(email, subject, body):
    """Mock email sending task"""
    print(f"Start sending email to {email}...")
    time.sleep(5) # Simulate delay
    print(f"Email sent to {email}!")
    return f"Sent to {email}"

@shared_task(ignore_result=False)
def add_task(x, y):
    return x + y

# 导入仓库同步任务
from app.services.warehouse.sync_service import sync_all_third_party_warehouses

# 注意：不要在模块级别创建Celery实例，这会导致循环导入
# Celery实例将在运行时通过celery_utils创建

