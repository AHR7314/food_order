from django.conf import settings
from django.db import models
from restaurants.models import Restaurant, Food
from django.utils.translation import gettext_lazy as _


class DiscountCode(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE,
                                   related_name='discount_codes')
    code = models.CharField(max_length=20, unique=True)
    percent = models.PositiveIntegerField(help_text=_('Discount percent (1 to 100)'))
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    def __str__(self):
        return self.code


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'سبد {self.user.username}'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'food')

    def __str__(self):
        return f'{self.food.name} x {self.quantity}'


class Order(models.Model):
    class Status(models.TextChoices):
        PREPARING = 'preparing', _('Preparing')
        SENT = 'sent', _('Sent')
        DELIVERED = 'delivered', _('Delivered')
        CANCELED = 'canceled', _('Canceled')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='orders')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE,
                                   related_name='orders')
    discount_code = models.ForeignKey(DiscountCode, on_delete=models.SET_NULL,
                                      null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices,
                              default=Status.PREPARING)
    delivery_address = models.TextField()
    total_price = models.DecimalField(max_digits=12, decimal_places=0)
    final_price = models.DecimalField(max_digits=12, decimal_places=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'سفارش {self.id} - {self.user.username}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    food = models.ForeignKey(Food, on_delete=models.SET_NULL, null=True)
    food_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.food_name} x {self.quantity}'