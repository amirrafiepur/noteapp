from django.contrib.auth import login
from django.shortcuts import redirect
from django.views.generic import FormView

from .forms import RegisterForm


class RegisterView(FormView):
    template_name = 'accounts/register.html'
    form_class = RegisterForm

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('dashboard')
