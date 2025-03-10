release: python migrations_manager.py
web: gunicorn --worker-class gevent -w 1 app:app