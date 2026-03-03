"""
Celery application configuration.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "voice_agent",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
    task_default_queue="default",
    task_routes={
        "app.worker.tasks.process_extraction": {"queue": "extraction"},
        "app.worker.tasks.export_to_excel_task": {"queue": "export"},
        "app.worker.tasks.export_to_sheets_task": {"queue": "export"},
        "app.worker.tasks.initiate_outbound_call": {"queue": "calls"},
        "app.worker.tasks.post_call_processing": {"queue": "extraction"},
        "app.worker.tasks.check_custom_server_health": {"queue": "health"},
    },
    beat_schedule={
        "health-check-custom-servers": {
            "task": "app.worker.tasks.periodic_health_check",
            "schedule": 30.0,
        },
        "run-scheduled-exports": {
            "task": "app.worker.tasks.run_scheduled_exports",
            "schedule": 60.0,  # Check every minute
        },
    },
)
