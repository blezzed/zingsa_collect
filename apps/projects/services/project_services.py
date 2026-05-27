from django.db import transaction
from apps.projects.models import Project, ProjectMember
import uuid

@transaction.atomic
def create_project_service(
    name: str,
    code: str = None,
    description: str = None,
    organization = None,
    owner = None,
    status: str = 'draft'
) -> Project:
    """
    Creates and saves a Project instance, and assigns the owner as a Manager.
    Generates a unique code if none is provided.
    """
    if not code:
        code = f"PROJ-{uuid.uuid4().hex[:6].upper()}"
    project = Project(
        name=name,
        code=code,
        description=description,
        organization=organization,
        owner=owner,
        status=status
    )
    project.full_clean()
    project.save()
    
    if owner:
        ProjectMember.objects.create(
            project=project,
            user=owner,
            role='manager'
        )
        
    return project
