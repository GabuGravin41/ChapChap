from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.utils import timezone
from datetime import datetime, timedelta
from .publisher import publish_scheduled_posts
import logging

logger = logging.getLogger(__name__)

def start_scheduler():
    """Start the background scheduler for content publishing"""
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        # Run every 5 minutes to check for new content to publish
        scheduler.add_job(
            publish_scheduled_posts,
            'interval',
            minutes=5,
            id='publish_scheduled_content',
            jobstore='default',
            replace_existing=True
        )
        
        # Run daily to update analytics
        scheduler.add_job(
            update_analytics,
            'cron',
            hour=0,  # Midnight
            minute=0,
            id='update_daily_analytics',
            jobstore='default',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("Scheduler started successfully")
        return scheduler
    except Exception as e:
        logger.error(f"Error in start_scheduler: {e}")
        raise e

def update_analytics():
    """Update analytics for all published posts"""
    from ..models import PublishedPost
    cutoff_time = timezone.now() - timedelta(days=1)
    logger.info(f"Running scheduled analytics update for posts after {cutoff_time}")
    
    # Get recent posts
    recent_posts = PublishedPost.objects.filter(
        published_at__gte=cutoff_time,
        published_id__isnull=False
    )
    
    # In a real implementation, this would call the platform APIs
    from . import analytics
    for post in recent_posts:
        # Update engagement metrics
        analytics.track_engagement(post)
    
    logger.info(f"Analytics update completed for {recent_posts.count()} posts")
