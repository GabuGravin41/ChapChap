from django.apps import AppConfig
import sys
import logging

logger = logging.getLogger(__name__)

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        # Start the scheduler when the app is ready
        # Skip startup during management commands (like migrate)
        import os
        if 'runserver' not in sys.argv:
            return
            
        # Only start once in main thread
        if os.environ.get('RUN_MAIN', None) != 'true':
            return
            
        try:
            from .agents.scheduler import start_scheduler
            logger.info("Starting background scheduler...")
            start_scheduler()
            logger.info("Background scheduler started successfully")
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            print(f"Error starting scheduler: {e}")
