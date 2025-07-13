from django.db import migrations

def update_twitter_to_x(apps, schema_editor):
    """Update existing Twitter platform data to X"""
    SocialAccount = apps.get_model('core', 'SocialAccount')
    Content = apps.get_model('core', 'Content')
    PublishedPost = apps.get_model('core', 'PublishedPost')
    
    # Update SocialAccount platform codes
    SocialAccount.objects.filter(platform='TW').update(platform='X')
    
    # Update Content platforms JSON field
    for content in Content.objects.all():
        if content.platforms and 'TW' in content.platforms:
            content.platforms = [p if p != 'TW' else 'X' for p in content.platforms]
            content.save()
    
    # Update PublishedPost platform codes
    PublishedPost.objects.filter(platform='TW').update(platform='X')

def reverse_update_x_to_twitter(apps, schema_editor):
    """Reverse the migration - update X back to TW"""
    SocialAccount = apps.get_model('core', 'SocialAccount')
    Content = apps.get_model('core', 'Content')
    PublishedPost = apps.get_model('core', 'PublishedPost')
    
    # Reverse SocialAccount platform codes
    SocialAccount.objects.filter(platform='X').update(platform='TW')
    
    # Reverse Content platforms JSON field
    for content in Content.objects.all():
        if content.platforms and 'X' in content.platforms:
            content.platforms = [p if p != 'X' else 'TW' for p in content.platforms]
            content.save()
    
    # Reverse PublishedPost platform codes
    PublishedPost.objects.filter(platform='X').update(platform='TW')

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(update_twitter_to_x, reverse_update_x_to_twitter),
    ] 