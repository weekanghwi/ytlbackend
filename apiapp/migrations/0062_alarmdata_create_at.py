# Generated by Django 4.2.4 on 2024-06-26 03:56

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('apiapp', '0061_alarmdata'),
    ]

    operations = [
        migrations.AddField(
            model_name='alarmdata',
            name='create_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]