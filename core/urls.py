from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('create/', views.create, name='create'),
    path('analytics/', views.analytics, name='analytics'),
    path('accounts/', views.accounts, name='accounts'),
    path('settings/', views.settings, name='settings'),
    path('posts/', views.all_posts, name='all_posts'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('connect/<str:platform>/', views.connect_platform, name='connect_platform'),
    path('disconnect/<int:platform_id>/', views.disconnect_platform, name='disconnect_platform'),
    path('refresh-account/<int:account_id>/', views.refresh_account, name='refresh_account'),
    path('generate-preview/', views.generate_preview, name='generate_preview'),
    path('delete-content/<int:content_id>/', views.delete_content, name='delete_content'),
    path('publish-now/<int:post_id>/', views.publish_now, name='publish_now'),
    path('run-scheduler/', views.run_scheduler, name='run_scheduler'),
    path('save-draft/', views.save_draft, name='save_draft'),
    path('refresh-account/<int:account_id>/', views.refresh_account, name='refresh_account'),
]