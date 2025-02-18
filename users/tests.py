from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailAuthBackendTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='securepassword'
        )

    def test_authenticate_with_email(self):
        from general import EmailAuthBackend
        backend = EmailAuthBackend()
        user = backend.authenticate(request=None, email='test@example.com', password='securepassword')
        self.assertIsNotNone(user)
        self.assertEqual(user, self.user)

    def test_authenticate_with_invalid_email(self):
        from general import EmailAuthBackend
        backend = EmailAuthBackend()
        user = backend.authenticate(request=None, email='invalid@example.com', password='securepassword')
        self.assertIsNone(user)

    def test_authenticate_with_invalid_password(self):
        from general import EmailAuthBackend
        backend = EmailAuthBackend()
        user = backend.authenticate(request=None, email='test@example.com', password='wrongpassword')
        self.assertIsNone(user)
