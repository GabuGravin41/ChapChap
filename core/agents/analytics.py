"""Analytics collection and processing."""
import logging
from datetime import datetime, timedelta
import requests
from textblob import TextBlob
from django.utils import timezone
from ..models import PublishedPost, SocialAccount

logger = logging.getLogger(__name__)

def collect_metrics(user=None):
    """Collect metrics for published posts."""
    try:
        # Get posts to update (last 30 days)
        cutoff = timezone.now() - timedelta(days=30)
        query = PublishedPost.objects.filter(published_at__gte=cutoff)
        if user:
            query = query.filter(content__user=user)
        
        posts = query.select_related('content')
        updated_users = set()
        
        for post in posts:
            try:
                # Get metrics from platform
                metrics = fetch_platform_metrics(
                    platform=post.platform,
                    post_id=post.published_id,
                    access_token=get_access_token(post.content.user, post.platform)
                )
                
                if metrics:
                    # Update metrics including sentiment
                    if not metrics.get('sentiment'):
                        metrics['sentiment'] = analyze_sentiment(post.adapted_text)
                    
                    # Keep error data if it exists
                    if post.metrics and post.metrics.get('error'):
                        metrics['error'] = post.metrics['error']
                        
                    post.metrics = metrics
                    post.save()
                    
                    updated_users.add(post.content.user)
                    
                    logger.info(f"Updated metrics for post {post.id} on {post.platform}")
                    
            except Exception as e:
                logger.error(f"Error collecting metrics for post {post.id}: {str(e)}")
                # Don't overwrite existing metrics on error
        
        # Send WebSocket updates for users with updated metrics
        if updated_users:
            send_analytics_updates(updated_users)
        
        return True
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        return False

def send_analytics_updates(users):
    """Send WebSocket updates to users with updated analytics."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("No channel layer configured for WebSocket updates")
            return
        
        for user in users:
            try:
                # Get fresh analytics data
                analytics_data = get_user_analytics_data(user)
                
                # Send to user's analytics group
                group_name = f"analytics_{user.id}"
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'analytics_update',
                        'data': analytics_data
                    }
                )
                
                logger.info(f"Sent analytics update to user {user.username}")
                
            except Exception as e:
                logger.error(f"Error sending analytics update to user {user.username}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error setting up WebSocket updates: {str(e)}")

def get_user_analytics_data(user):
    """Get analytics data for a specific user."""
    try:
        published_posts = PublishedPost.objects.filter(
            content__user=user
        ).order_by('-published_at')
        
        # Calculate summary metrics
        summary = {
            'likes': 0,
            'shares': 0,
            'comments': 0,
            'posts': published_posts.count(),
            'positive': 0,
            'neutral': 0,
            'negative': 0
        }
        
        # Platform engagement data
        platform_engagement = {p[0]: {'likes': 0, 'shares': 0, 'comments': 0} 
                              for p in SocialAccount.PLATFORM_CHOICES}
        
        # Recent activity for timeline
        recent_activity = []
        
        for post in published_posts:
            if post.metrics:
                summary['likes'] += post.metrics.get('likes', 0)
                summary['shares'] += post.metrics.get('shares', 0)
                summary['comments'] += post.metrics.get('comments', 0)
                
                # Update platform engagement
                platform = post.platform
                if platform in platform_engagement:
                    platform_engagement[platform]['likes'] += post.metrics.get('likes', 0)
                    platform_engagement[platform]['shares'] += post.metrics.get('shares', 0)
                    platform_engagement[platform]['comments'] += post.metrics.get('comments', 0)
                
                # Sentiment analysis
                sentiment = post.metrics.get('sentiment', 0.5)
                if sentiment > 0.6:
                    summary['positive'] += 1
                elif sentiment < 0.4:
                    summary['negative'] += 1
                else:
                    summary['neutral'] += 1
                
                # Recent activity
                recent_activity.append({
                    'id': post.id,
                    'platform': post.get_platform_display(),
                    'text': post.adapted_text[:100] + '...' if len(post.adapted_text) > 100 else post.adapted_text,
                    'published_at': post.published_at.isoformat() if post.published_at else None,
                    'metrics': {
                        'likes': post.metrics.get('likes', 0),
                        'shares': post.metrics.get('shares', 0),
                        'comments': post.metrics.get('comments', 0),
                    }
                })
        
        # Sort recent activity by date
        recent_activity.sort(key=lambda x: x['published_at'] or '', reverse=True)
        recent_activity = recent_activity[:10]  # Limit to 10 items
        
        return {
            'summary': summary,
            'platform_engagement': platform_engagement,
            'recent_activity': recent_activity,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics data for user {user.username}: {str(e)}")
        return {
            'summary': {'likes': 0, 'shares': 0, 'comments': 0, 'posts': 0},
            'platform_engagement': {},
            'recent_activity': [],
            'error': str(e)
        }

def fetch_platform_metrics(platform, post_id, access_token):
    """Fetch metrics from specific platform API."""
    if not all([platform, post_id, access_token]):
        return None
        
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        if platform == 'FB':  # Facebook
            url = f"https://graph.facebook.com/v18.0/{post_id}/insights"
            params = {
                "metric": "post_impressions,post_reactions,post_shares,post_comments",
                "period": "lifetime"
            }
            
        elif platform == 'X':  # X (Twitter)
            url = f"https://api.twitter.com/2/tweets/{post_id}?tweet.fields=public_metrics"
            params = {}
            
        elif platform == 'IG':  # Instagram
            url = f"https://graph.facebook.com/v18.0/{post_id}/insights"
            params = {
                "metric": "impressions,reach,saved,engagement"
            }
            
        elif platform == 'LI':  # LinkedIn
            url = f"https://api.linkedin.com/v2/socialActions/{post_id}"
            params = {}
            
        else:
            logger.warning(f"Metrics collection not implemented for {platform}")
            return None
        
        # Make API request
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Extract metrics based on platform
        if platform == 'FB':
            return {
                'likes': sum(d['values'][0]['value'] for d in data['data'] if 'reactions' in d['name']),
                'shares': sum(d['values'][0]['value'] for d in data['data'] if 'shares' in d['name']),
                'comments': sum(d['values'][0]['value'] for d in data['data'] if 'comments' in d['name']),
                'impressions': sum(d['values'][0]['value'] for d in data['data'] if 'impressions' in d['name'])
            }
            
        elif platform == 'X':
            metrics = data['data']['public_metrics']
            return {
                'likes': metrics['like_count'],
                'shares': metrics['retweet_count'],
                'comments': metrics['reply_count'],
                'impressions': metrics['impression_count']
            }
            
        elif platform == 'IG':
            return {
                'likes': sum(d['values'][0]['value'] for d in data['data'] if 'likes' in d['name']),
                'comments': sum(d['values'][0]['value'] for d in data['data'] if 'comments' in d['name']),
                'saves': sum(d['values'][0]['value'] for d in data['data'] if 'saved' in d['name']),
                'reach': sum(d['values'][0]['value'] for d in data['data'] if 'reach' in d['name'])
            }
            
        elif platform == 'LI':
            return {
                'likes': data.get('likesSummary', {}).get('totalLikes', 0),
                'comments': data.get('commentsSummary', {}).get('totalComments', 0),
                'shares': data.get('sharesSummary', {}).get('totalShares', 0)
            }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed for {platform}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error processing metrics for {platform}: {str(e)}")
        return None

def analyze_sentiment(text):
    """Analyze text sentiment using TextBlob."""
    try:
        analysis = TextBlob(text)
        # Convert polarity (-1 to 1) to a 0-1 scale
        return (analysis.sentiment.polarity + 1) / 2
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {str(e)}")
        return 0.5  # Neutral sentiment as fallback

def get_access_token(user, platform):
    """Helper to get access token."""
    try:
        account = SocialAccount.objects.get(user=user, platform=platform)
        return account.access_token
    except SocialAccount.DoesNotExist:
        return None