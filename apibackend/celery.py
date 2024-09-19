from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Django의 기본 설정 모듈을 Celery의 기본 설정으로 사용합니다.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apibackend.settings')

app = Celery('apibackend')

# 여기서 문자열을 사용한 이유는 작업자가 Celery 인스턴스를 자식 프로세스로 실행할 때 사용되기 때문입니다.
app.config_from_object('django.conf:settings', namespace='CELERY')

# 모든 등록된 Django 앱 설정에서 task 모듈을 불러옵니다.
app.autodiscover_tasks(['tasks'])

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
