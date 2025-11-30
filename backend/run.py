from app import create_app

app = create_app()
celery = app.extensions["celery"] # Expose for worker: celery -A run.celery worker

if __name__ == '__main__':
    app.run()
