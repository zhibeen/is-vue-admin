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

