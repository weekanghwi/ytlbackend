# Generated by Django 4.2.4 on 2023-09-04 01:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apiapp', '0013_alter_sitelsminfo_channelcard_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='siteretinfo',
            old_name='antidsubunitid',
            new_name='antidsubnetid',
        ),
        migrations.RenameField(
            model_name='siteretinfo',
            old_name='connectbordtype',
            new_name='connectboardtype',
        ),
        migrations.AlterField(
            model_name='siteretinfo',
            name='siteid',
            field=models.CharField(blank=True, editable=False, max_length=15),
        ),
    ]
