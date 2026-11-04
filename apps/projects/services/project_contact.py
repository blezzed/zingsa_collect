"""Project contact details shown to collectors."""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from rest_framework.exceptions import ValidationError

PROJECT_CONTACT_FIELDS = (
    "contact_name",
    "contact_phone",
    "contact_email",
    "contact_note",
)

PROJECT_CONTACT_LIMITS = {
    "contact_name": 150,
    "contact_phone": 30,
    "contact_email": 254,
    "contact_note": 300,
}

# Optional leading +, then digits, spaces, hyphens, or brackets.
_PHONE_PATTERN = re.compile(r"^\+?[\d\s\-()]+$")

_CONTACT_UNREACHABLE = (
    "Add a phone number or email so collectors can reach this contact."
)


def _contact_text(value) -> tuple[str, str | None]:
    if value is None:
        return "", None
    if not isinstance(value, str):
        return "", "Enter text."
    return value.strip(), None


def _phone_error(phone: str) -> str | None:
    if not _PHONE_PATTERN.fullmatch(phone):
        return (
            "Use digits, spaces, hyphens or brackets, with an optional leading +."
        )
    digits = re.sub(r"\D", "", phone)
    if not 7 <= len(digits) <= 15:
        return "Enter a phone number with 7 to 15 digits."
    return None


def normalize_project_contact(values: dict) -> dict[str, str]:
    """
    Trim contact fields and enforce the opt-in rules.

    A name or note with no phone and no email is refused. All four blank
    is a clear. Phone and email may be stored on their own.
    """
    cleaned: dict[str, str] = {}
    errors = {}
    for field, limit in PROJECT_CONTACT_LIMITS.items():
        text, type_error = _contact_text(values.get(field, ""))
        if type_error:
            errors[field] = type_error
            continue
        if len(text) > limit:
            errors[field] = f"Must be at most {limit} characters."
            continue
        cleaned[field] = text

    phone = cleaned.get("contact_phone", "")
    if "contact_phone" not in errors and phone:
        phone_error = _phone_error(phone)
        if phone_error:
            errors["contact_phone"] = phone_error

    email = cleaned.get("contact_email", "")
    if "contact_email" not in errors and email:
        try:
            validate_email(email)
        except DjangoValidationError:
            errors["contact_email"] = "Enter a valid email address."

    if errors:
        raise ValidationError(errors)

    if (cleaned["contact_name"] or cleaned["contact_note"]) and not (phone or email):
        raise ValidationError({"non_field_errors": _CONTACT_UNREACHABLE})

    return cleaned


def project_contact_block(project, user) -> dict[str, str] | None:
    """
    Read-only contact for form detail, the project form list, available, and download.

    Logged-out callers always get null, even on a demo form. A signed-in
    caller gets null only when all four fields on the project are blank.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return None
    name = (project.contact_name or "").strip()
    phone = (project.contact_phone or "").strip()
    email = (project.contact_email or "").strip()
    note = (project.contact_note or "").strip()
    if not any((name, phone, email, note)):
        return None
    return {"name": name, "phone": phone, "email": email, "note": note}


def contact_suggestion_for_owner(owner) -> dict[str, str]:
    """Owner account details for the edit form. Not stored on the project."""
    name = (owner.get_full_name() or "").strip() or (owner.username or "")
    return {"name": name, "email": owner.email or ""}
