from django.apps import AppConfig
import sys
import logging

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        if 'runserver' not in sys.argv:
            return
            
        # Prevent multiple scheduler instances during development reloads
        import os
        if os.environ.get('RUN_MAIN') != 'true':
            return
            
        # Import dependencies inside ready() to avoid AppRegistryNotReady error
        from django.conf import settings
        from apscheduler.schedulers.background import BackgroundScheduler
        from django_apscheduler.jobstores import DjangoJobStore, register_events
        from django_apscheduler.models import DjangoJobExecution
        from datetime import datetime, timedelta
        
        # Import our tasks
        from .agents.publisher import publish_content
        from .agents.analytics import collect_metrics
        from .models import PublishedPost, Content
        
        global scheduler
        if scheduler is None:
            try:
                # Create scheduler instance
                scheduler = BackgroundScheduler(settings.SCHEDULER_CONFIG)
                
                try:
                    # Add jobstore
                    scheduler.add_jobstore(DjangoJobStore(), "default")
                except ValueError as e:
                    if "already exists" not in str(e):
                        raise
                    logger.info("Default jobstore already exists")
                
                # Clean up old job executions
                def clean_old_job_executions():
                    try:
                        DjangoJobExecution.objects.delete_old_job_executions(
                            max_age=timedelta(days=7)
                        )
                        logger.info("Cleaned up old job executions")
                    except Exception as e:
                        logger.error(f"Error cleaning job executions: {str(e)}")
                
                # Add scheduled tasks
                def check_and_publish_scheduled():
                    """Check for and publish scheduled content."""
                    from django.utils import timezone
                    now = timezone.now()
                    logger.info("Checking for scheduled posts...")
                    
                    try:
                        # Get content scheduled for the next 5 minutes
                        upcoming = Content.objects.filter(
                            scheduled_time__lte=now + timedelta(minutes=5),
                            scheduled_time__gt=now - timedelta(minutes=5),
                            is_draft=False
                        ).select_related('user')
                        
                        for content in upcoming:
                            try:
                                publish_content(content)
                            except Exception as e:
                                logger.error(f"Failed to publish scheduled content {content.id}: {str(e)}")
                    except Exception as e:
                        logger.error(f"Error checking scheduled posts: {str(e)}")
                
                def update_metrics():
                    """Update metrics for recent posts."""
                    try:
                        logger.info("Updating post metrics...")
                        collect_metrics()
                    except Exception as e:
                        logger.error(f"Error updating metrics: {str(e)}")
                
                # Schedule jobs with replace_existing=True to handle reloads
                scheduler.add_job(
                    check_and_publish_scheduled,
                    trigger="interval",
                    minutes=1,
                    id="publish_scheduled_posts",
                    max_instances=1,
                    replace_existing=True,
                )
                
                scheduler.add_job(
                    update_metrics,
                    trigger="interval",
                    minutes=30,  # Run every 30 minutes
                    id="update_metrics",
                    max_instances=1,
                    replace_existing=True,
                )
                
                scheduler.add_job(
                    clean_old_job_executions,
                    trigger="cron",
                    hour="*/24",  # Run daily
                    id="clean_old_job_executions",
                    max_instances=1,
                    replace_existing=True,
                )
                
                # Register events with scheduler
                register_events(scheduler)
                
                # Start scheduler
                try:
                    logger.info("Starting scheduler...")
                    scheduler.start()
                except KeyboardInterrupt:
                    logger.info("Shutting down scheduler...")
                    scheduler.shutdown()
                    
            except Exception as e:
                logger.error(f"Error initializing scheduler: {str(e)}")
                if scheduler:
                    try:
                        scheduler.shutdown()
                    except:
                        pass
        else:
            logger.info("Scheduler already running.")
