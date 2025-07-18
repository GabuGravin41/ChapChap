# Generated by Django 4.2.23 on 2025-06-29 19:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Content',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_text', models.TextField()),
                ('media', models.FileField(blank=True, null=True, upload_to='content_media/')),
                ('platforms', models.JSONField(default=list)),
                ('scheduled_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('tone', models.CharField(choices=[('professional', 'Professional'), ('casual', 'Casual'), ('enthusiastic', 'Enthusiastic')], default='professional', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timezone', models.CharField(choices=[('UTC', 'UTC'), ('EST', 'Eastern Time (US & Canada)'), ('PST', 'Pacific Time (US & Canada)'), ('GMT', 'London')], default='UTC', max_length=50)),
                ('tone_preference', models.CharField(choices=[('professional', 'Professional'), ('casual', 'Casual'), ('enthusiastic', 'Enthusiastic')], default='professional', max_length=20)),
                ('email_notifications', models.BooleanField(default=True)),
                ('push_notifications', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SocialAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(choices=[('FB', 'Facebook'), ('IG', 'Instagram'), ('TW', 'Twitter/X'), ('LI', 'LinkedIn'), ('TT', 'TikTok')], max_length=2)),
                ('access_token', models.TextField()),
                ('username', models.CharField(max_length=100)),
                ('connected_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PublishedPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(max_length=2)),
                ('adapted_text', models.TextField()),
                ('published_id', models.CharField(blank=True, max_length=100)),
                ('published_at', models.DateTimeField(auto_now_add=True)),
                ('metrics', models.JSONField(default=dict)),
                ('content', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='published_posts', to='core.content')),
            ],
        ),
    ]
