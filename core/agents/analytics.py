import time
from django.utils import timezone
import requests
import logging
from django.conf import settings
import random

logger = logging.getLogger(__name__)

def fetch_platform_metrics(published_post):
    """Fetch real metrics from platform API"""
    platform = published_post.platform
    
    try:
        # Get access token
        from ..models import SocialAccount
        try:
            account = SocialAccount.objects.get(user=published_post.content.user, platform=platform)
            access_token = account.access_token
        except SocialAccount.DoesNotExist:
            logger.error(f"No connected account found for {platform}")
            return generate_demo_metrics(published_post)
        
        # Twitter metrics
        if platform == 'TW':
            try:
                url = f"https://api.twitter.com/2/tweets/{published_post.published_id}?tweet.fields=public_metrics"
                headers = {"Authorization": f"Bearer {access_token}"}
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                metrics = res.json()['data']['public_metrics']
                return {
                    'likes': metrics.get('like_count', 0),
                    'retweets': metrics.get('retweet_count', 0),
                    'replies': metrics.get('reply_count', 0),
                    'impressions': metrics.get('impression_count', 0)
                }
            except Exception as e:
                logger.error(f"Error fetching Twitter metrics: {str(e)}")
                return generate_demo_metrics(published_post)
        
        # Facebook/Instagram metrics
        elif platform in ['FB', 'IG']:
            try:
                url = f"https://graph.facebook.com/v18.0/{published_post.published_id}/insights"
                params = {
                    'access_token': access_token,
                    'metric': 'engagement,impressions,reach'
                }
                res = requests.get(url, params=params, timeout=10)
                res.raise_for_status()
                insights = {item['name']: item['values'][0]['value'] for item in res.json()['data']}
                return {
                    'likes': insights.get('engagement', 0),
                    'impressions': insights.get('impressions', 0),
                    'reach': insights.get('reach', 0)
                }
            except Exception as e:
                logger.error(f"Error fetching Facebook/Instagram metrics: {str(e)}")
                return generate_demo_metrics(published_post)
        
        # LinkedIn metrics
        elif platform == 'LI':
            try:
                url = f"https://api.linkedin.com/v2/ugcPosts/{published_post.published_id}"
                headers = {"Authorization": f"Bearer {access_token}"}
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                data = res.json()
                return {
                    'likes': data.get('likesSummary', {}).get('totalLikes', 0),
                    'comments': data.get('commentsSummary', {}).get('totalFirstLevelComments', 0),
                    'views': data.get('viewCount', 0)
                }
            except Exception as e:
                logger.error(f"Error fetching LinkedIn metrics: {str(e)}")
                return generate_demo_metrics(published_post)
                
        # For other platforms or if we don't have a specific implementation
        return generate_demo_metrics(published_post)
    
    except Exception as e:
        logger.error(f"Failed to fetch metrics for {platform}: {str(e)}")
        return generate_demo_metrics(published_post)

def generate_demo_metrics(published_post):
    """Generate realistic demo metrics for development/demo purposes"""
    if hasattr(published_post, 'id'):
        base = published_post.id % 10
        return {
            'likes': 5 + base + random.randint(0, 20),
            'shares': 1 + (base // 2) + random.randint(0, 5),
            'comments': (base // 3) + random.randint(0, 3),
            'views': 50 + (base * 10) + random.randint(20, 100),
            'sentiment': 0.5 + (random.randint(-20, 20) / 100),
            'note': 'Simulated metrics'
        }
    return {
        'likes': random.randint(5, 25),
        'shares': random.randint(1, 7),
        'comments': random.randint(0, 4),
        'views': random.randint(50, 150),
        'sentiment': 0.5 + (random.randint(-20, 20) / 100),
        'note': 'Simulated metrics'
    }

def track_engagement(published_post):
    """Track engagement for a published post"""
    logger.info(f"Tracking engagement for post {published_post.id} on {published_post.platform}")
    
    try:
        # For demo, update metrics immediately with simulated data
        if not settings.DEBUG:
            # In production, use threads for real API calls
            from threading import Thread
            Thread(target=delayed_metrics_update, args=(published_post.id,)).start()
        else:
            # For development/demo, update immediately with simulated data
            current_metrics = published_post.metrics or {}
            
            # Generate new metrics with some randomness for demo
            new_metrics = fetch_platform_metrics(published_post)
            
            # Preserve sentiment if it exists
            sentiment = current_metrics.get('sentiment', 0.7)
            
            # Update with new metrics
            published_post.metrics = {**new_metrics, 'sentiment': sentiment}
            published_post.save()
            logger.info(f"Updated metrics for post {published_post.id}: {new_metrics}")
    except Exception as e:
        logger.error(f"Error in track_engagement: {str(e)}")
        # Don't let metrics tracking failure affect the user experience
        # Just log the error and continue
        try:
            # Still try to update with demo metrics if possible
            if not published_post.metrics:
                published_post.metrics = generate_demo_metrics(published_post)
                published_post.save()
        except Exception as save_error:
            logger.error(f"Also failed to save demo metrics: {str(save_error)}")
            # At this point, we've done all we can

def delayed_metrics_update(post_id):
    """Update metrics after a delay to get actual engagement"""
    from ..models import PublishedPost
    
    # In production, wait for metrics to accumulate
    time.sleep(60)  # Reduced for demo, would be longer in production
    
    try:
        post = PublishedPost.objects.get(id=post_id)
        try:
            real_metrics = fetch_platform_metrics(post)
            if real_metrics:
                # Preserve simulated sentiment if exists
                current_metrics = post.metrics or {}
                sentiment = current_metrics.get('sentiment')
                
                # Update with real metrics
                post.metrics = {**real_metrics, 'sentiment': sentiment}
                post.save()
                logger.info(f"Updated delayed metrics for post {post_id}")
        except Exception as metrics_error:
            logger.error(f"Error fetching delayed metrics for post {post_id}: {str(metrics_error)}")
            # Still ensure we have some metrics
            if not post.metrics:
                post.metrics = generate_demo_metrics(post)
                post.save()
                logger.warning(f"Used fallback demo metrics for post {post_id}")
    except PublishedPost.DoesNotExist:
        logger.warning(f"Post {post_id} not found for metrics update")
    except Exception as e:
        logger.error(f"Unexpected error in delayed metrics update: {str(e)}")