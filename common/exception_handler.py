"""
Global DRF exception handler for ZINGSA Collect.
"""

import logging

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import DatabaseError, IntegrityError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler

from common.exceptions import CollectAPIException
from common.responses import build_error_response, format_exception_response

logger = logging.getLogger(__name__)


def _django_validation_to_errors(exc: DjangoValidationError) -> tuple[str, dict | None]:
    if hasattr(exc, "message_dict") and exc.message_dict:
        errors = {
            key: [str(msg) for msg in msgs] if isinstance(msgs, (list, tuple)) else [str(msgs)]
            for key, msgs in exc.message_dict.items()
        }
        return "Validation failed.", errors
    if hasattr(exc, "messages"):
        messages = exc.messages
        if isinstance(messages, list):
            return messages[0] if messages else "Validation failed.", None
        return str(messages), None
    return str(exc), None


def collect_exception_handler(exc, context):
    """Format all API errors into a consistent JSON envelope."""
    if isinstance(exc, CollectAPIException):
        return build_error_response(
            status_code=exc.status_code,
            code=exc.error_code,
            message=str(exc.detail),
            errors=exc.field_errors,
        )

    if isinstance(exc, Http404):
        return build_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="not_found",
            message=str(exc) or "Resource not found.",
        )

    if isinstance(exc, DjangoPermissionDenied):
        return build_error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="permission_denied",
            message=str(exc) or "You do not have permission to perform this action.",
        )

    if isinstance(exc, DjangoValidationError):
        message, errors = _django_validation_to_errors(exc)
        return build_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="validation_error",
            message=message,
            errors=errors,
        )

    if isinstance(exc, IntegrityError):
        logger.warning("IntegrityError: %s", exc, exc_info=exc)
        return build_error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="conflict",
            message="A database constraint was violated. The resource may already exist.",
        )

    response = drf_exception_handler(exc, context)

    if response is not None:
        return format_exception_response(response, exc)

    if isinstance(exc, DatabaseError):
        logger.exception("Database error")
        return build_error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="database_error",
            message="A database error occurred. Please try again later.",
        )

    try:
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError:
        BotoCoreError = ClientError = ()  # type: ignore[misc, assignment]

    if isinstance(exc, (BotoCoreError, ClientError)):
        logger.warning("Object storage error: %s", exc, exc_info=exc)
        return build_error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="storage_error",
            message="File storage is unavailable. Please try again later.",
        )

    # Unhandled exception
    logger.exception("Unhandled API exception", exc_info=exc)
    return build_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="internal_error",
        message="An unexpected server error occurred.",
    )
