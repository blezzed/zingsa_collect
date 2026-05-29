from django.db import transaction
from apps.organizations.models import Organization, OrganizationMember
import uuid

@transaction.atomic
def create_organization_service(
    name: str, 
    description: str = None,
    contact_email: str = None,
    phone_number: str = None,
    address: str = None,
    user=None
) -> Organization:
    """
    Creates an organization and assigns the given user as an Admin.
    Generates a unique code automatically.
    """
    code = f"ORG-{uuid.uuid4().hex[:6].upper()}"
        
    org = Organization(
        name=name, 
        code=code,
        description=description,
        contact_email=contact_email,
        phone_number=phone_number,
        address=address
    )
    org.full_clean()
    org.save()

    if user:
        OrganizationMember.objects.create(
            organization=org,
            user=user,
            role='admin'
        )

    return org
