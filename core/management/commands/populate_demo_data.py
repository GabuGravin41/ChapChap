from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from core.models import SocialAccount, Content, PublishedPost, UserSettings
import random

class Command(BaseCommand):
    help = 'Populate database with demo data'

    def handle(self, *args, **options):
        # Create or get demo user
        user, created = User.objects.get_or_create(
            username='demo',
            defaults={
                'email': 'demo@chapchap.com',
                'first_name': 'Demo',
                'last_name': 'User'
            }
        )
        if created:
            user.set_password('demo123')
            user.save()
            self.stdout.write(f'Created demo user: {user.username}')
        
        # Create user settings
        settings, created = UserSettings.objects.get_or_create(
            user=user,
            defaults={
                'timezone': 'EST',
                'tone_preference': 'professional',
                'email_notifications': True,
                'push_notifications': False
            }
        )
        
        # Create social accounts
        platforms = ['TW', 'IG', 'LI', 'FB']
        usernames = ['demo_twitter', 'demo_instagram', 'demo_linkedin', 'demo_facebook']
        
        for platform, username in zip(platforms, usernames):
            account, created = SocialAccount.objects.get_or_create(
                user=user,
                platform=platform,
                defaults={
                    'username': username,
                    'access_token': f'demo_token_{platform}_{user.id}',
                    'connected_at': timezone.now() - timedelta(days=random.randint(1, 30))
                }
            )
            if created:
                self.stdout.write(f'Created {platform} account for {user.username}')
        
        # Create sample content and posts
        sample_contents = [
            {
                'text': 'Just launched our new AI-powered social media management tool! 🚀 Perfect for busy entrepreneurs who want consistent brand presence.',
                'tone': 'enthusiastic',
                'platforms': ['X', 'IG', 'LI']
            },
            {
                'text': 'Sharing insights from our latest product development cycle. Key learnings about user-centered design and agile methodology.',
                'tone': 'professional',
                'platforms': ['LI', 'X']
            },
            {
                'text': 'Behind the scenes at ChapChap! Our team working hard to bring you the best social media automation experience.',
                'tone': 'casual',
                'platforms': ['IG', 'FB']
            },
            {
                'text': 'Tips for effective social media scheduling: Consistency is key, engagement matters more than followers, and authentic content wins.',
                'tone': 'professional',
                'platforms': ['X', 'LI', 'IG']
            },
            {
                'text': 'Weekend vibes! Taking time to reflect on our journey and plan for exciting features coming next month.',
                'tone': 'casual',
                'platforms': ['IG', 'FB']
            }
        ]
        
        for i, content_data in enumerate(sample_contents):
            # Create past, current, and future content
            if i < 2:
                # Past content (published)
                scheduled_time = timezone.now() - timedelta(days=random.randint(1, 7))
                is_published = True
            elif i == 2:
                # Current content (publishing now)
                scheduled_time = timezone.now() + timedelta(minutes=random.randint(-30, 30))
                is_published = False
            else:
                # Future content (scheduled)
                scheduled_time = timezone.now() + timedelta(days=random.randint(1, 14))
                is_published = False
            
            content, created = Content.objects.get_or_create(
                user=user,
                original_text=content_data['text'],
                defaults={
                    'platforms': content_data['platforms'],
                    'scheduled_time': scheduled_time,
                    'tone': content_data['tone'],
                    'is_draft': False
                }
            )
            
            if created:
                self.stdout.write(f'Created content: {content.original_text[:50]}...')
                
                # Create published posts for each platform
                for platform in content_data['platforms']:
                    adapted_text = self.adapt_content_for_platform(content_data['text'], platform)
                    
                    post = PublishedPost.objects.create(
                        content=content,
                        platform=platform,
                        adapted_text=adapted_text,
                        scheduled_time=scheduled_time
                    )
                    
                    if is_published:
                        post.published_at = scheduled_time + timedelta(minutes=random.randint(0, 10))
                        post.metrics = {
                            'likes': random.randint(10, 150),
                            'shares': random.randint(2, 25),
                            'comments': random.randint(1, 15),
                            'sentiment': round(random.uniform(0.6, 0.9), 2)
                        }
                        post.save()
                        self.stdout.write(f'  Published to {platform} with engagement metrics')
        
        # Create some draft content
        draft_content = Content.objects.create(
            user=user,
            original_text="Draft: Thinking about our next big announcement. Should we reveal the new features now or wait for the perfect moment?",
            platforms=['TW', 'LI'],
            tone='casual',
            is_draft=True,
            scheduled_time=timezone.now() + timedelta(days=3)
        )
        self.stdout.write(f'Created draft content')
        
        self.stdout.write(self.style.SUCCESS('Successfully populated demo data!'))
        self.stdout.write(f'Demo user credentials: username=demo, password=demo123')

    def adapt_content_for_platform(self, text, platform):
        """Simple content adaptation for demo purposes"""
        adaptations = {
            'TW': f"{text[:200]}... #SocialMedia #AI #Automation",
            'IG': f"{text}\n\n#ChapChap #SocialMedia #AI #Entrepreneurship #Productivity",
            'LI': f"{text}\n\nAs professionals in the digital space, we understand the challenges of maintaining consistent social presence. What are your thoughts on AI-powered content management?",
            'FB': f"{text}\n\nWe'd love to hear your thoughts! Comment below with your social media challenges."
        }
        return adaptations.get(platform, text)
