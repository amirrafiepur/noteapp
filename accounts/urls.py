from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .forms import LoginForm
from .views import RegisterView

urlpatterns = [
    path(
        'login/',
        LoginView.as_view(
            template_name='accounts/login.html',
            authentication_form=LoginForm,
        ),
        name='login',
    ),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
