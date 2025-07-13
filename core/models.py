from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class SocialAccount(models.Model):
    PLATFORM_CHOICES = [
        ('FB', 'Facebook'),
        ('IG', 'Instagram'),
        ('X', 'X (Twitter)'),
        ('LI', 'LinkedIn'),
        ('TT', 'TikTok'),
        ('YT', 'YouTube'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.CharField(max_length=2, choices=PLATFORM_CHOICES)
    access_token = models.TextField()
    username = models.CharField(max_length=100)
    connected_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s {self.get_platform_display()}"

class Content(models.Model):
    TONE_CHOICES = [
        ('professional', 'Professional'),
        ('casual', 'Casual'),
        ('enthusiastic', 'Enthusiastic'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    original_text = models.TextField()
    media = models.FileField(upload_to='content_media/', blank=True, null=True)
    platforms = models.JSONField(default=list)  # ['FB', 'X', etc.]
    scheduled_time = models.DateTimeField(default=timezone.now)
    tone = models.CharField(max_length=20, choices=TONE_CHOICES, default='professional')
    created_at = models.DateTimeField(auto_now_add=True)
    is_draft = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Content by {self.user.username} at {self.scheduled_time}"

class PublishedPost(models.Model):
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='published_posts')
    platform = models.CharField(max_length=2)
    adapted_text = models.TextField()
    published_id = models.CharField(max_length=100, blank=True)  # Platform's post ID
    published_at = models.DateTimeField(auto_now_add=True)
    scheduled_time = models.DateTimeField(default=timezone.now)
    metrics = models.JSONField(default=dict)  # {'likes': 10, 'shares': 2, etc.}
    
    def __str__(self):
        return f"Published on {self.get_platform_display()} at {self.published_at}"

class UserSettings(models.Model):
    TIMEZONE_CHOICES = [
        ('UTC', 'UTC'),
        ('EST', 'Eastern Time (US & Canada)'),
        ('PST', 'Pacific Time (US & Canada)'),
        ('GMT', 'London'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES, default='UTC')
    tone_preference = models.CharField(
        max_length=20, 
        choices=Content.TONE_CHOICES, 
        default='professional'
    )
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Settings for {self.user.username}"