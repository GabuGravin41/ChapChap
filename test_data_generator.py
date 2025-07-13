#!/usr/bin/env python
"""
Test data generator for ChapChap analytics demo
Creates sample posts with realistic metrics for demonstration
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chapchap.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Content, PublishedPost, SocialAccount

def create_test_data():
    """Create test data for analytics demonstration."""
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"Created test user: {user.username}")
    
    # Create some social accounts
    platforms = ['X', 'FB', 'IG', 'LI']
    for platform in platforms:
        account, created = SocialAccount.objects.get_or_create(
            user=user,
            platform=platform,
            defaults={
                'access_token': f'test_token_{platform}',
                'username': f'test_user_{platform}'
            }
        )
        if created:
            print(f"Created {platform} account")
    
    # Create test content and published posts
    test_posts = [
        {
            'text': 'Exciting news! Our new product launch is getting amazing feedback from early users. The community support has been incredible! 🚀',
            'platforms': ['X', 'FB', 'IG', 'LI'],
            'days_ago': 1
        },
        {
            'text': 'Behind the scenes of our latest project. The team worked tirelessly to bring this vision to life. Proud of what we accomplished together!',
            'platforms': ['IG', 'LI'],
            'days_ago': 2
        },
        {
            'text': 'Quick industry update: The latest trends in social media marketing are fascinating. Here\'s what we\'re seeing...',
            'platforms': ['X', 'LI'],
            'days_ago': 3
        },
        {
            'text': 'Customer spotlight: Amazing success story from one of our clients. Their growth over the past year has been phenomenal!',
            'platforms': ['FB', 'LI'],
            'days_ago': 4
        },
        {
            'text': 'Weekend vibes! Taking a moment to appreciate the journey and all the lessons learned along the way. 🌟',
            'platforms': ['IG', 'FB'],
            'days_ago': 5
        }
    ]
    
    for post_data in test_posts:
        # Create content
        content = Content.objects.create(
            user=user,
            original_text=post_data['text'],
            platforms=post_data['platforms'],
            scheduled_time=timezone.now() - timedelta(days=post_data['days_ago']),
            tone='professional',
            is_draft=False
        )
        
        # Create published posts for each platform
        for platform in post_data['platforms']:
            published_post = PublishedPost.objects.create(
                content=content,
                platform=platform,
                adapted_text=post_data['text'],
                published_id=f"test_post_{platform}_{content.id}",
                published_at=timezone.now() - timedelta(days=post_data['days_ago']),
                scheduled_time=content.scheduled_time,
                metrics={
                    'likes': random.randint(10, 100),
                    'shares': random.randint(1, 20),
                    'comments': random.randint(0, 15),
                    'views': random.randint(100, 1000),
                    'sentiment': random.uniform(0.3, 0.9),
                    'note': 'Generated test data'
                }
            )
        
        print(f"Created test post: {content.original_text[:50]}...")
    
    # Create some scheduled posts for the future
    future_posts = [
        {
            'text': 'Upcoming webinar announcement! Join us next week for insights on the latest industry trends.',
            'platforms': ['X', 'LI'],
            'days_ahead': 2
        },
        {
            'text': 'Save the date! Our annual conference is coming up and we have some exciting speakers lined up.',
            'platforms': ['FB', 'LI'],
            'days_ahead': 5
        }
    ]
    
    for post_data in future_posts:
        content = Content.objects.create(
            user=user,
            original_text=post_data['text'],
            platforms=post_data['platforms'],
            scheduled_time=timezone.now() + timedelta(days=post_data['days_ahead']),
            tone='professional',
            is_draft=False
        )
        
        # Create scheduled posts (not yet published)
        for platform in post_data['platforms']:
            PublishedPost.objects.create(
                content=content,
                platform=platform,
                adapted_text=post_data['text'],
                published_id='',  # Empty for scheduled posts
                published_at=None,  # Not published yet
                scheduled_time=content.scheduled_time,
                metrics={}
            )
        
        print(f"Created scheduled post: {content.original_text[:50]}...")
    
    print("\nTest data generation complete!")
    print(f"Total content items: {Content.objects.filter(user=user).count()}")
    print(f"Total published posts: {PublishedPost.objects.filter(content__user=user).count()}")
    print(f"Test user credentials: username='testuser', password='testpass123'")

def update_metrics_demo():
    """Update metrics for demonstration of real-time updates."""
    
    # Get a random published post
    published_posts = PublishedPost.objects.filter(
        published_at__isnull=False
    ).exclude(metrics__isnull=True)
    
    if not published_posts.exists():
        print("No published posts found to update")
        return
    
    # Update metrics for a random post
    post = random.choice(published_posts)
    
    # Simulate metrics growth
    if post.metrics:
        post.metrics['likes'] = post.metrics.get('likes', 0) + random.randint(1, 10)
        post.metrics['shares'] = post.metrics.get('shares', 0) + random.randint(0, 3)
        post.metrics['comments'] = post.metrics.get('comments', 0) + random.randint(0, 2)
        post.metrics['updated_at'] = timezone.now().isoformat()
        post.save()
        
        print(f"Updated metrics for post {post.id}: {post.metrics}")
        
        # Trigger analytics update
        from core.agents.analytics import send_analytics_updates
        send_analytics_updates([post.content.user])
        
        return True
    
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'update':
        update_metrics_demo()
    else:
        create_test_data() 