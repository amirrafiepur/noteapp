from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


class LoginForm(AuthenticationForm):
    error_messages = {
        'invalid_login': 'نام کاربری یا رمز عبور اشتباه است. لطفاً دوباره تلاش کنید.',
        'inactive': 'این حساب کاربری غیرفعال است.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'نام کاربری'
        self.fields['password'].label = 'رمز عبور'
        self.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'نام کاربری خود را وارد کنید',
            'autocomplete': 'username',
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'رمز عبور خود را وارد کنید',
            'autocomplete': 'current-password',
        })
        self.fields['username'].error_messages = {
            'required': 'لطفاً نام کاربری را وارد کنید.',
        }
        self.fields['password'].error_messages = {
            'required': 'لطفاً رمز عبور را وارد کنید.',
        }


class RegisterForm(UserCreationForm):
    error_messages = {
        'password_mismatch': 'رمزهای عبور با یکدیگر مطابقت ندارند.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'نام کاربری'
        self.fields['password1'].label = 'رمز عبور'
        self.fields['password2'].label = 'تکرار رمز عبور'
        self.fields['password1'].help_text = (
            'رمز عبور باید حداقل ۸ کاراکتر باشد و نباید بیش از حد ساده یا '
            'شبیه اطلاعات شخصی شما باشد.'
        )
        self.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'نام کاربری دلخواه خود را وارد کنید',
            'autocomplete': 'username',
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'رمز عبور را وارد کنید',
            'autocomplete': 'new-password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'رمز عبور را دوباره وارد کنید',
            'autocomplete': 'new-password',
        })
        self.fields['username'].error_messages = {
            'required': 'لطفاً نام کاربری را وارد کنید.',
            'unique': 'این نام کاربری قبلاً استفاده شده است.',
            'invalid': 'نام کاربری معتبر نیست.',
        }
        self.fields['password1'].error_messages = {
            'required': 'لطفاً رمز عبور را وارد کنید.',
        }
        self.fields['password2'].error_messages = {
            'required': 'لطفاً تکرار رمز عبور را وارد کنید.',
        }
