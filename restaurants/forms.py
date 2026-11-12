from django import forms
from django.utils.translation import gettext_lazy as _

from accounts.forms import BootstrapMixin
from .models import Restaurant, Food


class RestaurantForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ('name', 'description', 'address', 'phone')
        labels = {
            'name': _('Name'),
            'description': _('Description'),
            'address': _('Address'),
            'phone': _('Phone number'),
        }
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}


class FoodForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Food
        fields = ('name', 'price', 'description', 'image', 'is_available')
        labels = {
            'name': _('Name'),
            'price': _('Price'),
            'description': _('Description'),
            'image': _('Image'),
            'is_available': _('Available'),
        }
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}