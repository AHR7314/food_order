from django import forms
from django.utils.translation import gettext_lazy as _

from accounts.forms import BootstrapMixin
from restaurants.models import Restaurant
from .models import DiscountCode


class CheckoutForm(BootstrapMixin, forms.Form):
    delivery_address = forms.CharField(
        label=_('Delivery address'),
        widget=forms.Textarea(attrs={'rows': 3}),
    )


class DiscountCodeForm(BootstrapMixin, forms.ModelForm):
    percent = forms.IntegerField(min_value=1, max_value=100, label=_('Discount percent'))

    class Meta:
        model = DiscountCode
        fields = ('restaurant', 'code', 'percent', 'is_active', 'valid_from', 'valid_to')
        labels = {
            'restaurant': _('Restaurant'),
            'code': _('Code'),
            'is_active': _('Active'),
            'valid_from': _('Valid from'),
            'valid_to': _('Valid until'),
        }
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'},
                                              format='%Y-%m-%dT%H:%M'),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local'},
                                            format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        # فقط رستوران‌های خود صاحب
        if owner is not None:
            self.fields['restaurant'].queryset = Restaurant.objects.filter(owner=owner)
        for name in ('valid_from', 'valid_to'):
            self.fields[name].input_formats = ['%Y-%m-%dT%H:%M']

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get('valid_from'), cleaned.get('valid_to')
        if start and end and end <= start:
            raise forms.ValidationError(_('End time must be after start time.'))
        return cleaned