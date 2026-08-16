from django.conf import settings
from django.db import models


class Note(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notes',
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', '-created_at']),
        ]

    def __str__(self):
        if not self.content:
            return f'Note {self.pk}'
        preview = self.content[:50]
        if len(self.content) > 50:
            preview += '...'
        return preview
