web: gunicorn app:app -w 4 --threads 12
scheduler: rqscheduler --url $REDIS_URL
worker: python worker.py