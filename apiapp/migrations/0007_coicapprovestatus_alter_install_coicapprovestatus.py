# Generated by Django 4.2.4 on 2023-08-30 09:22

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('apiapp', '0006_opttype'),
    ]

    operations = [
        migrations.CreateModel(
            name='COICApproveStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coiapprovestatus', models.CharField(max_length=20)),
                ('create_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('modify_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AlterField(
            model_name='install',
            name='coicapprovestatus',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='apiapp.coicapprovestatus'),
        ),
    ]
