from app import create_app
from app.cli import seed_db_command

app = create_app()
celery = app.extensions["celery"] # Expose for worker: celery -A run.celery worker
app.cli.add_command(seed_db_command)

if __name__ == '__main__':
    app.run()
