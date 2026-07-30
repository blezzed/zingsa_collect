from django import template
from apps.projects.models import Project
from apps.forms.models import Form
from apps.submissions.models import Submission
from django.contrib.auth import get_user_model

register = template.Library()

@register.simple_tag
def get_dashboard_stats():
    User = get_user_model()
    return {
        'project_count': Project.objects.filter(status='active').count(),
        'form_count': Form.objects.filter(status='published').count(),
        'submission_count': Submission.objects.count(),
        'user_count': User.objects.count(),
    }
