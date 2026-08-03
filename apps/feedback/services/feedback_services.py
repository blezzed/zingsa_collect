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
        page_url=(page_url or "").strip()[:500],
    )
    item.full_clean()
    item.save()
    return item


def list_feedback_for_user(user):
    """Own feedback for normal users; all feedback for Support+ staff."""
    qs = Feedback.objects.select_related("user").order_by("-created_at")
    if getattr(user, "can_view_all_feedback", lambda: False)():
        return qs
    return qs.filter(user=user)
