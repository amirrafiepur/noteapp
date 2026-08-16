from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import NoteForm
from .models import Note


@login_required
def dashboard(request):
    return render(
        request,
        'notes/dashboard.html',
        {
            'form': NoteForm(),
            'notes': request.user.notes.all(),
        },
    )


@login_required
@require_http_methods(['POST'])
def note_create(request):
    form = NoteForm(request.POST)
    if form.is_valid():
        note = form.save(commit=False)
        note.owner = request.user
        note.save()
        messages.success(request, 'متن با موفقیت ذخیره شد.')
        return redirect('dashboard')

    messages.error(request, 'ذخیره متن انجام نشد. لطفاً خطاها را بررسی کنید.')
    return render(
        request,
        'notes/dashboard.html',
        {
            'form': form,
            'notes': request.user.notes.all(),
        },
    )


@login_required
def note_detail(request, pk):
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    return render(
        request,
        'notes/note_detail.html',
        {
            'note': note,
        },
    )


@login_required
def note_print(request, pk):
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    return render(
        request,
        'notes/note_print.html',
        {
            'note': note,
        },
    )
