from django.contrib import admin
from .models import SocialAccount, Content, PublishedPost, UserSettings

@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'username', 'connected_at']
    list_filter = ['platform', 'connected_at']
    search_fields = ['user__username', 'username']

@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ['user', 'scheduled_time', 'tone', 'created_at']
    list_filter = ['tone', 'scheduled_time', 'created_at']
    search_fields = ['user__username', 'original_text']
    date_hierarchy = 'created_at'

@admin.register(PublishedPost)
class PublishedPostAdmin(admin.ModelAdmin):
    list_display = ['content', 'platform', 'published_at', 'published_id']
    list_filter = ['platform', 'published_at']
    search_fields = ['content__user__username', 'adapted_text', 'published_id']
    date_hierarchy = 'published_at'

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'timezone', 'tone_preference', 'email_notifications', 'push_notifications']
    list_filter = ['timezone', 'tone_preference', 'email_notifications', 'push_notifications']
    search_fields = ['user__username']
