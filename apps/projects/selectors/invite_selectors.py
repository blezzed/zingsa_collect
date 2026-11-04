from apps.projects.models.invite import ProjectInvite


def get_project_invites_selector(project):
    return (
        ProjectInvite.objects.filter(project=project)
        .select_related('created_by', 'project')
        .prefetch_related('joins__user')
        .order_by('-created_at')
    )


def get_project_invite_selector(project, invite_id):
    return get_project_invites_selector(project).filter(id=invite_id).first()
