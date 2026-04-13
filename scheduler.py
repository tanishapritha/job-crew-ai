"""
Scheduler — deferred import of CrewAI to allow the FastAPI server
to boot even when no LLM API key is configured.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()


def _run_campaign_wrapper():
    """Lazy import so CrewAI agents are only created when the campaign actually fires."""
    from crews.jobs_crew import run_campaign
    return run_campaign()


def start_scheduler():
    scheduler.add_job(
        _run_campaign_wrapper,
        'cron',
        hour=9,
        minute=0,
        timezone='Asia/Kolkata',
        id='daily_campaign',
        replace_existing=True,
    )
    scheduler.start()
    print("Scheduler started: campaign runs daily at 09:00 Asia/Kolkata")


def stop_scheduler():
    scheduler.shutdown()
    print("Scheduler stopped")
