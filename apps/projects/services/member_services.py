from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from apps.projects.models.member import ProjectMember

User = get_user_model()

def add_project_member_service(project, username: str, role: str) -> ProjectMember:
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise ValidationError({"username": ["User not found."]})

    member, created = ProjectMember.objects.get_or_create(
        project=project,
        user=user,
        defaults={'role': role}
    )
    
    if not created and member.role != role:
        member.role = role
        member.save()
        
    return member


def update_project_member_service(project, username: str, role: str) -> ProjectMember:
    try:
        member = ProjectMember.objects.get(project=project, user__username=username)
    except ProjectMember.DoesNotExist:
        raise ValidationError({"detail": "Member not found in this project."})

    member.role = role
    member.save()
    return member


def remove_project_member_service(project, username: str):
    try:
        member = ProjectMember.objects.get(project=project, user__username=username)
    except ProjectMember.DoesNotExist:
        raise ValidationError({"detail": "Member not found in this project."})

    member.delete()
