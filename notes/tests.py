from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Note

User = get_user_model()


class NoteOwnershipTests(TestCase):
    """Notes must never be readable by, or attributable to, another user."""

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass12345')
        self.other = User.objects.create_user(username='other', password='pass12345')
        self.note = Note.objects.create(owner=self.owner, content='یادداشت محرمانه')

    def test_note_detail_requires_login(self):
        response = self.client.get(reverse('note_detail', args=[self.note.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_note_print_requires_login(self):
        response = self.client.get(reverse('note_print', args=[self.note.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_owner_can_view_own_note_detail(self):
        self.client.login(username='owner', password='pass12345')
        response = self.client.get(reverse('note_detail', args=[self.note.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.note.content)

    def test_owner_can_view_own_note_print(self):
        self.client.login(username='owner', password='pass12345')
        response = self.client.get(reverse('note_print', args=[self.note.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.note.content)

    def test_other_user_cannot_view_note_detail(self):
        self.client.login(username='other', password='pass12345')
        response = self.client.get(reverse('note_detail', args=[self.note.pk]))
        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_view_note_print(self):
        self.client.login(username='other', password='pass12345')
        response = self.client.get(reverse('note_print', args=[self.note.pk]))
        self.assertEqual(response.status_code, 404)

    def test_note_create_ignores_client_supplied_owner(self):
        """The owner must always come from request.user, never client input."""
        self.client.login(username='owner', password='pass12345')
        self.client.post(
            reverse('note_create'),
            {'content': 'متن جدید', 'owner': self.other.pk},
        )
        created = Note.objects.get(content='متن جدید')
        self.assertEqual(created.owner, self.owner)

    def test_dashboard_lists_only_own_notes(self):
        Note.objects.create(owner=self.other, content='متن دیگری')
        self.client.login(username='owner', password='pass12345')
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, self.note.content)
        self.assertNotContains(response, 'متن دیگری')


class NotePrintPageTests(TestCase):
    """The print page must contain only the note, with no app chrome/nav."""

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass12345')
        self.note = Note.objects.create(owner=self.owner, content='محتوای چاپی')
        self.client.login(username='owner', password='pass12345')

    def test_print_page_has_no_dashboard_navigation(self):
        response = self.client.get(reverse('note_print', args=[self.note.pk]))
        self.assertNotContains(response, 'site-header')
        self.assertNotContains(response, 'بازگشت به داشبورد')

    def test_print_page_triggers_window_print(self):
        response = self.client.get(reverse('note_print', args=[self.note.pk]))
        self.assertContains(response, 'window.print()')

    def test_note_detail_has_print_link(self):
        response = self.client.get(reverse('note_detail', args=[self.note.pk]))
        self.assertContains(response, reverse('note_print', args=[self.note.pk]))
