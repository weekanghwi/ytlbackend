# Generated by Django 4.2.4 on 2023-09-22 02:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apiapp', '0034_fastatus_create_at'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='FAStatus',
            new_name='ReviewStatus',
        ),
    ]