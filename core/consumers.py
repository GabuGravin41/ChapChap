import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import PublishedPost, SocialAccount
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

class AnalyticsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Accept WebSocket connection for authenticated users"""
        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            self.user = self.scope["user"]
            self.group_name = f"analytics_{self.user.id}"
            
            # Join analytics group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Send initial analytics data
            analytics_data = await self.get_analytics_data()
            await self.send(text_data=json.dumps({
                'type': 'analytics_update',
                'data': analytics_data
            }))
            
            logger.info(f"Analytics WebSocket connected for user {self.user.username}")

    async def disconnect(self, close_code):
        """Leave analytics group"""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"Analytics WebSocket disconnected for user {self.user.username}")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'request_update':
                # Send fresh analytics data
                analytics_data = await self.get_analytics_data()
                await self.send(text_data=json.dumps({
                    'type': 'analytics_update',
                    'data': analytics_data
                }))
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received in WebSocket")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")

    async def analytics_update(self, event):
        """Send analytics update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'analytics_update',
            'data': event['data']
        }))

    @database_sync_to_async
    def get_analytics_data(self):
        """Get current analytics data for the user"""
        try:
            published_posts = PublishedPost.objects.filter(
                content__user=self.user
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
                'timestamp': json.dumps(timezone.now(), default=str)
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics data: {str(e)}")
            return {
                'summary': {'likes': 0, 'shares': 0, 'comments': 0, 'posts': 0},
                'platform_engagement': {},
                'recent_activity': [],
                'error': str(e)
            } 