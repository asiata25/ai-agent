APP_MODULE = app.main:app
CELERY_APP = app.worker:celery_app
HOST = 0.0.0.0
PORT = 8000

.PHONY: app worker

app:
	uv run uvicorn $(APP_MODULE) --host $(HOST) --port $(PORT) --reload

worker:
	uv run celery -A $(CELERY_APP) worker --loglevel=info
