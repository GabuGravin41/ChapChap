from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Scheduler Settings
SCHEDULER_CONFIG = {
    'apscheduler.jobstores.default': {
        'class': 'django_apscheduler.jobstores:DjangoJobStore'
    },
    'apscheduler.executors.default': {
        'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
        'max_workers': 5
    },
    'apscheduler.executors.processpool': {
        'type': 'processpool',
        'max_workers': 2
    },
    'apscheduler.job_defaults': {
        'coalesce': False,
        'max_instances': 1,
        'misfire_grace_time': 15*60  # 15 minutes grace time
    },
    'apscheduler.timezone': 'UTC'
}

# APScheduler Django configuration
APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"  # Default
APSCHEDULER_RUN_NOW_TIMEOUT = 25  # Seconds

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'apscheduler': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-i6=-)o1z4cx*0l%n1w4$4t&fc#t_2ghe6v5(fex-)t$!kh+e8d')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = ['*']  # Render will provide the actual host


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'core.apps.CoreConfig',
    'django_apscheduler',
    'channels',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'chapchap.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'core/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'chapchap.wsgi.application'
ASGI_APPLICATION = 'chapchap.asgi.application'

# Channels configuration for WebSocket support
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [os.getenv('REDIS_URL', 'redis://localhost:6379')],
        },
    },
}

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Whitenoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'  # This uses the name of your URL pattern
LOGIN_REDIRECT_URL = 'dashboard'  # Name of the URL to redirect after login
LOGOUT_REDIRECT_URL = 'login'     # Name of the URL to redirect after logout

# X (Twitter) API Configuration
X_API_KEY = os.getenv('X_API_KEY', '')
X_API_SECRET = os.getenv('X_API_SECRET', '')
X_ACCESS_TOKEN = os.getenv('X_ACCESS_TOKEN', '')
X_ACCESS_TOKEN_SECRET = os.getenv('X_ACCESS_TOKEN_SECRET', '')
X_BEARER_TOKEN = os.getenv('X_BEARER_TOKEN', '')

# X OAuth 2.0 Configuration (for user authentication)
X_CLIENT_ID = os.getenv('X_CLIENT_ID', '')
X_CLIENT_SECRET = os.getenv('X_CLIENT_SECRET', '')

# Validate X credentials in production
if not DEBUG and X_API_KEY:
    if not all([X_API_KEY, X_API_SECRET, X_BEARER_TOKEN]):
        import warnings
        warnings.warn("X API credentials incomplete. Social media posting may not work.", UserWarning)

# Social Media API Configuration
SOCIAL_MEDIA_APIS = {
    'X': {
        'api_key': X_API_KEY,
        'api_secret': X_API_SECRET,
        'access_token': X_ACCESS_TOKEN,
        'access_token_secret': X_ACCESS_TOKEN_SECRET,
        'bearer_token': X_BEARER_TOKEN,
        'base_url': 'https://api.twitter.com/2',
        'auth_type': 'oauth2',
        'rate_limits': {
            'tweets': {'limit': 300, 'window': 900},  # 300 per 15 minutes
            'users': {'limit': 75, 'window': 900}     # 75 per 15 minutes
        }
    },
    'FB': {
        'app_id': os.getenv('FACEBOOK_APP_ID', ''),
        'app_secret': os.getenv('FACEBOOK_APP_SECRET', ''),
        'base_url': 'https://graph.facebook.com/v18.0',
        'auth_type': 'oauth2'
    },
    'IG': {
        'app_id': os.getenv('INSTAGRAM_APP_ID', ''),
        'app_secret': os.getenv('INSTAGRAM_APP_SECRET', ''),
        'base_url': 'https://graph.facebook.com/v18.0',
        'auth_type': 'oauth2'
    },
    'LI': {
        'client_id': os.getenv('LINKEDIN_CLIENT_ID', ''),
        'client_secret': os.getenv('LINKEDIN_CLIENT_SECRET', ''),
        'base_url': 'https://api.linkedin.com/v2',
        'auth_type': 'oauth2'
    }
}

# AI Model Configuration for Content Adaptation
AI_CONFIG = {
    'default_model': 'mock',  # Use mock for demo
    'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
    'huggingface_api_key': os.getenv('HUGGINGFACE_API_KEY', ''),
    'openrouter_api_key': os.getenv('OPENROUTER_API_KEY', ''),
    'content_adaptation': {
        'max_retries': 3,
        'timeout': 30,
        'fallback_enabled': True
    }
}

# Content Publishing Configuration
PUBLISHING_CONFIG = {
    'max_retry_attempts': 3,
    'retry_delay_seconds': 300,  # 5 minutes
    'batch_size': 10,
    'rate_limit_delay': 1,  # seconds between API calls
    'enable_scheduling': True,
    'scheduler_interval_minutes': 5
}

# Analytics Collection Configuration
ANALYTICS_CONFIG = {
    'collection_enabled': True,
    'collection_interval_hours': 6,
    'retention_days': 90,
    'metrics_to_collect': ['likes', 'shares', 'comments', 'impressions', 'reach']
}

# Security Configuration
SECURITY_CONFIG = {
    'api_rate_limiting': True,
    'token_encryption': True,
    'audit_logging': True,
    'max_file_size_mb': 10,
    'allowed_file_types': ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov']
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    'cache_timeout': 300,  # 5 minutes
    'max_concurrent_posts': 5,
    'database_pool_size': 10,
    'enable_compression': True
}