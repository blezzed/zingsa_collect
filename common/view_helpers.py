"""
Helpers for API views — validation and resource lookup.
"""

from common.exceptions import ResourceNotFound, ValidationFailed


def require_fields(data: dict, *field_names: str, message: str | None = None) -> None:
    """Raise ValidationFailed if any named fields are missing or blank."""
    errors = {}
    for name in field_names:
        value = data.get(name)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors[name] = [message or "This field is required."]
    if errors:
        raise ValidationFailed(errors=errors)


def require_non_empty_string(data: dict, field_name: str, *, label: str | None = None) -> str:
    """Return a stripped string or raise ValidationFailed."""
    value = data.get(field_name)
    if not value or not str(value).strip():
        raise ValidationFailed(
            errors={field_name: [f"{label or field_name} is required."]},
        )
    return str(value).strip()


def get_or_raise(not_found_message: str = "Resource not found."):
    """Decorator factory: raise ResourceNotFound when a selector returns None."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if result is None:
                raise ResourceNotFound(not_found_message)
            return result

        return wrapper

    return decorator


def raise_if_missing(obj, message: str = "Resource not found."):
    if obj is None:
        raise ResourceNotFound(message)
    return obj
