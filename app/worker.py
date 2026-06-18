from celery import Celery
from app.core.settings import settings

celery_app = Celery(
    "worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Autodiscover tasks inside each module folder
celery_app.autodiscover_tasks([
    "app.modules.visualization",
])
