from django.test import TestCase, RequestFactory
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from django.core.exceptions import ValidationError as DjangoValidationError

from common.exception_handler import collect_exception_handler
from common.exceptions import ResourceNotFound, ValidationFailed, BusinessRuleError


class ErrorEnvelopeTests(TestCase):
    def _handle(self, exc, view=None):
        request = RequestFactory().get('/api/test/')
        view = view or APIView()
        context = {'view': view, 'request': request}
        return collect_exception_handler(exc, context)

    def test_resource_not_found_envelope(self):
        response = self._handle(ResourceNotFound('Project not found.'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'not_found')
        self.assertEqual(response.data['error']['message'], 'Project not found.')
        self.assertEqual(response.data['detail'], 'Project not found.')

    def test_validation_failed_with_field_errors(self):
        response = self._handle(
            ValidationFailed(
                errors={'name': ['This field is required.']},
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'validation_error')
        self.assertEqual(response.data['error']['errors']['name'], ['This field is required.'])

    def test_business_rule_error(self):
        response = self._handle(BusinessRuleError('Form does not have a version to publish.'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'business_rule_violation')

    def test_drf_not_found_normalized(self):
        response = self._handle(NotFound('Not found.'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])

    def test_permission_denied_normalized(self):
        response = self._handle(PermissionDenied())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error']['code'], 'permission_denied')

    def test_drf_validation_error_normalized(self):
        response = self._handle(
            ValidationError({'title': ['This field is required.']}),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data['error']['errors'])

    def test_django_validation_error_normalized(self):
        exc = DjangoValidationError({'code': ['Organization code already exists.']})
        response = self._handle(exc)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['error']['errors']['code'],
            ['Organization code already exists.'],
        )

    def test_unhandled_exception_returns_500(self):
        response = self._handle(RuntimeError('unexpected'))
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['error']['code'], 'internal_error')
        self.assertFalse(response.data['success'])
