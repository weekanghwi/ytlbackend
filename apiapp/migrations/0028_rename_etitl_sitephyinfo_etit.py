# Generated by Django 4.2.4 on 2023-09-07 01:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apiapp', '0027_sitephyinfo_etitl'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sitephyinfo',
            old_name='etitl',
            new_name='etit',
        ),
    ]