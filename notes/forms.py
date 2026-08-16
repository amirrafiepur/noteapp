from django import forms

from .models import Note


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['content']
        labels = {
            'content': 'متن',
        }
        error_messages = {
            'content': {
                'required': 'لطفاً متن یادداشت را وارد کنید.',
            },
        }
        widgets = {
            'content': forms.Textarea(
                attrs={
                    'rows': 8,
                    'class': 'form-textarea',
                    'placeholder': 'متن جدید را اینجا بنویسید...',
                },
            ),
        }
