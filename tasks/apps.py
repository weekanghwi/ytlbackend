from django.apps import AppConfig
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
        from .tasks import cache_same_pci_filtered_results
        schedule, create = CrontabSchedule.objects.get_or_create(
            minute='0',
            hou='0',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )
        PeriodicTask.objects.get_or_create(
            crontab=schedule,
            name='Cache same pci filtered results every midnight',
            task='tasks.tasks.cache_same_pci_filtered_results',
            args=json.dump([10])
        )
