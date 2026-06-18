APP_MODULE = app.main:app
CELERY_APP = app.worker:celery_app
HOST = 0.0.0.0
PORT = 8000
LOG_DIR = logs

.PHONY: app worker redis stop status start logs-app logs-worker help

help:
	@echo "Available commands:"
	@echo "  make start       - Start ALL services (Redis, Celery, FastAPI) in the background"
	@echo "  make stop        - Stop the Redis server, Celery worker, and FastAPI server"
	@echo "  make status      - Check the status of Redis and python processes"
	@echo "  make logs-app    - Tail the FastAPI application logs"
	@echo "  make logs-worker - Tail the Celery worker logs"
	@echo ""
	@echo "Or run in the foreground (recommended for development):"
	@echo "  make redis       - Start Redis server in the background (if not already running)"
	@echo "  make app         - Run the FastAPI application in the foreground"
	@echo "  make worker      - Run the Celery background worker in the foreground"

redis:
	@echo "Checking Redis status..."
	@redis-cli ping >/dev/null 2>&1 || (echo "Starting Redis server..." && redis-server --daemonize yes)

app: redis
	@echo "Starting FastAPI App on $(HOST):$(PORT)..."
	uv run uvicorn $(APP_MODULE) --host $(HOST) --port $(PORT) --reload

worker: redis
	@echo "Starting Celery Worker..."
	uv run celery -A $(CELERY_APP) worker --loglevel=info

start: redis
	@mkdir -p $(LOG_DIR)
	@echo "Starting Celery worker in background (logging to $(LOG_DIR)/celery.log)..."
	@nohup uv run celery -A $(CELERY_APP) worker --loglevel=info > $(LOG_DIR)/celery.log 2>&1 &
	@echo "Starting FastAPI app in background (logging to $(LOG_DIR)/uvicorn.log)..."
	@nohup uv run uvicorn $(APP_MODULE) --host $(HOST) --port $(PORT) --reload > $(LOG_DIR)/uvicorn.log 2>&1 &
	@echo "All services started in background."
	@echo "Tailing FastAPI server logs..."
	@sleep 1
	@tail -n 20 $(LOG_DIR)/uvicorn.log

logs-app:
	@mkdir -p $(LOG_DIR)
	@touch $(LOG_DIR)/uvicorn.log
	tail -f $(LOG_DIR)/uvicorn.log

logs-worker:
	@mkdir -p $(LOG_DIR)
	@touch $(LOG_DIR)/celery.log
	tail -f $(LOG_DIR)/celery.log

stop:
	@echo "Shutting down Redis server..."
	@-redis-cli shutdown >/dev/null 2>&1 || true
	@echo "Stopping running Celery workers..."
	@-pkill -f "celery" >/dev/null 2>&1 || true
	@echo "Stopping running Uvicorn processes..."
	@-pkill -f "uvicorn" >/dev/null 2>&1 || true
	@echo "All services stopped."

status:
	@echo "=== Redis Status ==="
	@-redis-cli ping 2>/dev/null || echo "Redis is offline"
	@echo "\n=== Python Processes ==="
	@ps aux | grep -E "uvicorn|celery" | grep -v grep || echo "No active uvicorn or celery processes found."
