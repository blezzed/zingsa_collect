from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from apps.organizations.models.member import OrganizationMember

User = get_user_model()

def add_org_member_service(organization, username: str, role: str) -> OrganizationMember:
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise ValidationError({"username": ["User not found."]})

    member, created = OrganizationMember.objects.get_or_create(
        organization=organization,
        user=user,
        defaults={'role': role}
    )
    
    if not created and member.role != role:
        member.role = role
        member.save()
        
    return member


def update_org_member_service(organization, username: str, role: str) -> OrganizationMember:
    try:
        member = OrganizationMember.objects.get(organization=organization, user__username=username)
    except OrganizationMember.DoesNotExist:
        raise ValidationError({"detail": "Member not found in this organization."})

    member.role = role
    member.save()
    return member


def remove_org_member_service(organization, username: str):
    try:
        member = OrganizationMember.objects.get(organization=organization, user__username=username)
    except OrganizationMember.DoesNotExist:
        raise ValidationError({"detail": "Member not found in this organization."})

    # Optional: Prevent removing the last admin?
    if member.role == 'admin':
        admin_count = OrganizationMember.objects.filter(organization=organization, role='admin').count()
        if admin_count <= 1:
            raise ValidationError({"detail": "Cannot remove the last administrator of the organization."})

    member.delete()
