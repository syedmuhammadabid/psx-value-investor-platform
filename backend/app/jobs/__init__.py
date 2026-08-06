"""Scheduled and background jobs (APScheduler).

The scheduler is started and stopped via the FastAPI lifespan in ``app.main``.
Import ``scheduler`` from ``app.jobs.scheduler`` to interact with it directly
(e.g. for testing or manual job invocation).
"""
