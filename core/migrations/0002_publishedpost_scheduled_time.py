from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='publishedpost',
            name='scheduled_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
