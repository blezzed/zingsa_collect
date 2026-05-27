from django.db import transaction
from apps.organizations.models import Organization, OrganizationMember
import uuid

@transaction.atomic
def create_organization_service(name: str, code: str = None, user=None) -> Organization:
    """
    Creates an organization and assigns the given user as an Admin.
    Generates a unique code if none is provided.
    """
    if not code:
        code = f"ORG-{uuid.uuid4().hex[:6].upper()}"
        
    org = Organization(name=name, code=code)
    org.full_clean()
    org.save()

    if user:
        OrganizationMember.objects.create(
            organization=org,
            user=user,
            role='admin'
        )

    return org
