# Generated by Django 4.2.4 on 2023-11-17 02:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apiapp', '0056_alter_statisticcalculated_uid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='statisticcalculated',
            name='uid',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
