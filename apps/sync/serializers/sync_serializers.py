from rest_framework import serializers
from apps.sync.models import SyncLog

class SyncLogSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = SyncLog
        fields = [
            'id', 'user', 'user_username', 'device_id', 'project', 
            'form', 'total_received', 'total_success', 'total_failed', 
            'conflict_count', 'started_at', 'finished_at', 'log'
        ]
        read_only_fields = fields
