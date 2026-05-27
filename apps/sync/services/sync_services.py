from django.db import transaction
from django.utils import timezone

from apps.sync.models import SyncLog
from apps.forms.models import FormVersion
from apps.submissions.services.submission_services import sync_submission_to_physical_table_service

def bulk_sync_submissions_service(
    device_id: str,
    submissions_list: list,
    project = None,
    form = None,
    user = None
) -> dict:
    """
    Processes multiple submissions in an atomic way with transaction savepoints.
    Logs success, duplicates, and failures in a comprehensive SyncLog.
    """
    started_at = timezone.now()
    total_received = len(submissions_list)
    total_success = 0
    total_failed = 0
    conflict_count = 0
    logs = []
    
    for idx, sub_data in enumerate(submissions_list):
        client_submission_id = sub_data.get('client_submission_id')
        version_id = sub_data.get('form_version_id')
        answers = sub_data.get('answers', {})
        
        if not client_submission_id or not version_id:
            total_failed += 1
            logs.append({
                'index': idx,
                'client_submission_id': client_submission_id,
                'status': 'failed',
                'error': 'Missing client_submission_id or form_version_id.'
            })
            continue
            
        try:
            form_version = FormVersion.objects.get(id=version_id)
        except FormVersion.DoesNotExist:
            total_failed += 1
            logs.append({
                'index': idx,
                'client_submission_id': client_submission_id,
                'status': 'failed',
                'error': f"Form version '{version_id}' not found."
            })
            continue
            
        try:
            with transaction.atomic():
                sub_index, is_duplicate = sync_submission_to_physical_table_service(
                    client_submission_id=client_submission_id,
                    device_id=device_id,
                    form_version=form_version,
                    answers=answers,
                    user=user
                )
                
                if is_duplicate:
                    conflict_count += 1
                    logs.append({
                        'index': idx,
                        'client_submission_id': client_submission_id,
                        'status': 'duplicate',
                        'submission_id': str(sub_index.id),
                        'message': 'Submission already synced.'
                    })
                else:
                    total_success += 1
                    logs.append({
                        'index': idx,
                        'client_submission_id': client_submission_id,
                        'status': 'success',
                        'submission_id': str(sub_index.id)
                    })
        except Exception as e:
            total_failed += 1
            logs.append({
                'index': idx,
                'client_submission_id': client_submission_id,
                'status': 'failed',
                'error': str(e)
            })
            
    finished_at = timezone.now()
    
    sync_log = SyncLog.objects.create(
        user=user,
        device_id=device_id,
        project=project,
        form=form,
        total_received=total_received,
        total_success=total_success,
        total_failed=total_failed,
        conflict_count=conflict_count,
        started_at=started_at,
        finished_at=finished_at,
        log={'details': logs}
    )
    
    return {
        'sync_log_id': str(sync_log.id),
        'total_received': total_received,
        'total_success': total_success,
        'total_failed': total_failed,
        'conflict_count': conflict_count,
        'started_at': started_at.isoformat(),
        'finished_at': finished_at.isoformat(),
        'submissions': logs
    }
