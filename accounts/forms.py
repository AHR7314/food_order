from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _

from .models import User


class BootstrapMixin:
    """به همه‌ی فیلدهای فرم کلاس Bootstrap می‌دهد."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = 'form-check-input'
            elif isinstance(widget, forms.Select):
                widget.attrs['class'] = 'form-select'
            else:
                widget.attrs['class'] = 'form-control'


class SignUpForm(BootstrapMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'phone', 'address', 'role')
        labels = {
            'username': _('Username'),
            'email': _('Email'),
            'phone': _('Phone number'),
            'address': _('Address'),
            'role': _('Account type'),
        }
        widgets = {'address': forms.Textarea(attrs={'rows': 3})}


class LoginForm(BootstrapMixin, AuthenticationForm):
    pass