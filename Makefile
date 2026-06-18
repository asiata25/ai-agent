APP_MODULE = app.api:app
HOST = 0.0.0.0
PORT = 8000

.PHONY: app

app:
	uv run uvicorn $(APP_MODULE) --host $(HOST) --port $(PORT) --reload
