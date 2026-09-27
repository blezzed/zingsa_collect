from django.utils import timezone

from apps.feedback.models import Feedback


def create_feedback_service(
    *,
    user,
    subject: str,
    message: str,
    category: str = Feedback.Category.IMPROVEMENT,
    page_url: str = "",
) -> Feedback:
    item = Feedback(
        user=user,
        subject=subject,
        message=message,
        category=category or Feedback.Category.IMPROVEMENT,
        status=Feedback.Status.OPEN,
        page_url=(page_url or "").strip()[:500],
    )
    item.full_clean()
    item.save()
    return item


def list_feedback_for_user(user):
    """Own feedback for normal users; all feedback for Support+ staff."""
    qs = Feedback.objects.select_related("user", "resolved_by").order_by(
        "-created_at"
    )
    if getattr(user, "can_view_all_feedback", lambda: False)():
        return qs
    return qs.filter(user=user)


def update_feedback_status_service(
    *, item: Feedback, status: str, actor, note: str = ""
) -> Feedback:
    valid = {c.value for c in Feedback.Status}
    if status not in valid:
        raise ValueError("Invalid feedback status.")

    cleaned_note = (note or "").strip()
    if status == Feedback.Status.IGNORED:
        if not cleaned_note:
            raise ValueError("Add a reason to ignore this feedback.")
        item.status_note = cleaned_note[:2000]
        item.resolved_at = timezone.now()
        item.resolved_by = actor
    elif status == Feedback.Status.SOLVED:
        item.status_note = cleaned_note[:2000]
        item.resolved_at = timezone.now()
        item.resolved_by = actor
    else:
        item.status_note = ""
        item.resolved_at = None
        item.resolved_by = None

    item.status = status
    item.save(
        update_fields=[
            "status",
            "status_note",
            "resolved_at",
            "resolved_by",
            "updated_at",
        ]
    )
    return item
