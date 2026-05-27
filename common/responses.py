"""
Standard API error response builders for ZINGSA Collect.
"""

from typing import Any

from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList


def _stringify_detail(detail: Any) -> str:
    if detail is None:
        return "An error occurred."
    if isinstance(detail, (list, tuple)):
        return _stringify_detail(detail[0]) if detail else "An error occurred."
    if isinstance(detail, dict):
        if "detail" in detail:
            return _stringify_detail(detail["detail"])
        messages = []
        for value in detail.values():
            if isinstance(value, (list, tuple)):
                messages.extend(str(v) for v in value)
            else:
                messages.append(str(value))
        return "; ".join(messages) if messages else "Validation failed."
    return str(detail)


def _extract_field_errors(data: Any) -> dict | None:
    if isinstance(data, ReturnDict):
        data = dict(data)
    if isinstance(data, ReturnList):
        return None
    if not isinstance(data, dict):
        return None
    if set(data.keys()) == {"detail"}:
        return None
    field_errors = {}
    for key, value in data.items():
        if key == "detail":
            continue
        if isinstance(value, (list, tuple)):
            field_errors[key] = [str(v) for v in value]
        else:
            field_errors[key] = [str(value)]
    return field_errors or None


def build_error_payload(
    *,
    code: str,
    message: str,
    errors: dict | None = None,
) -> dict:
    payload = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "errors": errors,
        },
        "detail": message,
    }
    if errors:
        payload.update(errors)
    return payload


def build_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    errors: dict | None = None,
) -> Response:
    return Response(
        build_error_payload(code=code, message=message, errors=errors),
        status=status_code,
    )


def format_exception_response(response: Response, exc: Exception) -> Response:
    """Normalize a DRF-generated error response into the standard envelope."""
    data = response.data
    field_errors = _extract_field_errors(data)
    message = _stringify_detail(data)

    code = getattr(exc, "error_code", None) or getattr(exc, "default_code", "error")
    if hasattr(code, "value"):
        code = str(code)

    response.data = build_error_payload(
        code=str(code),
        message=message,
        errors=field_errors,
    )
    return response
