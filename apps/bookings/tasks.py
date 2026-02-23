"""
Celery tasks for booking management.
"""

import logging

from django.core.management import call_command

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="bookings.expire_draft_bookings")
def expire_draft_bookings():
    """
    Celery task to expire DRAFT bookings past their expiry time.

    Schedule this task to run every 5 minutes:

    # In celery.py or settings.py:
    CELERY_BEAT_SCHEDULE = {
        'expire-draft-bookings': {
            'task': 'bookings.expire_draft_bookings',
            'schedule': crontab(minute='*/5'),  # Every 5 minutes
        },
    }
    """
    try:
        logger.info("Starting booking expiry task")
        call_command("expire_bookings")
        logger.info("Booking expiry task completed successfully")
    except Exception as e:
        logger.error(f"Booking expiry task failed: {str(e)}")
        raise


@shared_task(name="bookings.cleanup_expired_drafts")
def cleanup_expired_drafts():
    """
    PHASE 4: Celery task to cleanup expired booking drafts.

    Deletes all drafts that have passed their 24h TTL.

    Schedule this task to run every hour:

    # In celery.py or settings.py:
    CELERY_BEAT_SCHEDULE = {
        'cleanup-expired-drafts': {
            'task': 'bookings.cleanup_expired_drafts',
            'schedule': crontab(minute=0),  # Every hour
        },
    }
    """
    try:
        from .models_draft import BookingDraft

        logger.info("Starting draft cleanup task")
        expired_count = BookingDraft.cleanup_expired()
        logger.info(f"Draft cleanup completed: {expired_count} expired drafts deleted")

        return {
            "success": True,
            "deleted_count": expired_count,
        }
    except Exception as e:
        logger.error(f"Draft cleanup task failed: {str(e)}")
        raise
