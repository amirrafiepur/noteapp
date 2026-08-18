from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AuthFlowTests(TestCase):
    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'a-strong-pass-1',
            'password2': 'a-strong-pass-1',
        })
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_with_valid_credentials(self):
        User.objects.create_user(username='amir', password='pass12345')
        response = self.client.post(reverse('login'), {
            'username': 'amir',
            'password': 'pass12345',
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_with_invalid_credentials_shows_persian_error(self):
        User.objects.create_user(username='amir', password='pass12345')
        response = self.client.post(reverse('login'), {
            'username': 'amir',
            'password': 'wrong-password',
        })
        self.assertContains(response, 'نام کاربری یا رمز عبور اشتباه است')

    def test_logout_redirects_to_login(self):
        User.objects.create_user(username='amir', password='pass12345')
        self.client.login(username='amir', password='pass12345')
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)
