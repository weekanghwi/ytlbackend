import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class ProgressConsumer(WebsocketConsumer):
  def connect(self):
    self.accept()
    async_to_sync(self.channel_layer.group_add)(
      'progress_group',
      self.channel_name
    )

  def disconnect(self, close_code):
    async_to_sync(self.channel_layer.group_discard)(
      'progress_group',
      self.channel_name
    )

  def receive(self, text_data):
    data = json.loads(text_data)
    pass

  def send_progress(self, event):
    progress = event['progress']
    self.send(text_data=json.dumps({
      'progress': progress
    }))