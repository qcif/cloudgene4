import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Job

User = get_user_model()


class JobStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.job_id = self.scope['url_route']['kwargs']['job_id']
        self.job_group_name = f'job_{self.job_id}'

        # Check if user has permission to view this job
        if await self.can_access_job():
            await self.channel_layer.group_add(
                self.job_group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close(code=403)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.job_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Handle incoming WebSocket messages if needed
        pass

    async def job_status_update(self, event):
        """Send job status updates to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'job_status',
            'job_id': event['job_id'],
            'status': event['status'],
            'progress': event.get('progress'),
            'message': event.get('message'),
            'timestamp': event.get('timestamp'),
        }))

    async def job_log_update(self, event):
        """Send job log updates to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'job_log',
            'job_id': event['job_id'],
            'log_line': event['log_line'],
            'timestamp': event.get('timestamp'),
        }))

    @database_sync_to_async
    def can_access_job(self):
        """Check if the current user can access this job"""
        try:
            user = self.scope['user']
            if not user.is_authenticated:
                return False
            
            job = Job.objects.get(id=self.job_id)
            return job.user == user or user.is_admin_user()
        except Job.DoesNotExist:
            return False