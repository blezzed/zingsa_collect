"""
Custom API exceptions for ZINGSA Collect.

Raise these from views and services; the global exception handler formats
consistent JSON error responses for all clients.
"""

from rest_framework.exceptions import APIException
from rest_framework import status


class CollectAPIException(APIException):
    """Base exception with a machine-readable error code and optional field errors."""

    default_code = "api_error"

    def __init__(self, message=None, *, code=None, errors=None):
        self.error_code = code or self.default_code
        self.field_errors = errors
        detail = message if message is not None else self.default_detail
        super().__init__(detail=detail)


class ResourceNotFound(CollectAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Resource not found."
    default_code = "not_found"


class ValidationFailed(CollectAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Validation failed."
    default_code = "validation_error"


class ConflictError(CollectAPIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Resource conflict."
    default_code = "conflict"


class BusinessRuleError(CollectAPIException):
    """Domain rule violation (e.g. form not publishable)."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Request could not be processed."
    default_code = "business_rule_violation"
