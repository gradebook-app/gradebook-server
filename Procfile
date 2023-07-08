web: gunicorn --max-requests 500 --max-requests-jitter 100 app:app -w 3 --preload
worker: python worker.py -q default,low