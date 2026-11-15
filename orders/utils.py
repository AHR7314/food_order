from django.utils import timezone
from django.utils.translation import gettext as _

from .models import DiscountCode

FINAL_STATUSES = ('delivered', 'canceled')

# انتقال‌های مجاز وضعیت سفارش (نمودار ۴)
ALLOWED_TRANSITIONS = {
    'preparing': ['sent', 'canceled'],
    'sent': ['delivered'],
    'delivered': [],
    'canceled': [],
}


def allowed_next_statuses(order):
    return ALLOWED_TRANSITIONS.get(order.status, [])


def validate_discount(code, restaurant):
    """چهار شرط نمودار ۲. خروجی: (کد تخفیف, پیام خطا)"""
    code = (code or '').strip()
    try:
        discount = DiscountCode.objects.get(code=code)
    except DiscountCode.DoesNotExist:
        return None, _('Invalid discount code.')
    if not discount.is_active:
        return None, _('This discount code is not active.')
    now = timezone.now()
    if not (discount.valid_from <= now <= discount.valid_to):
        return None, _('This discount code has expired or is not valid yet.')
    if discount.restaurant_id != restaurant.id:
        return None, _('This discount code cannot be used for this restaurant.')
    return discount, None


def calculate_prices(items, discount=None):
    """خروجی: (جمع کل, مبلغ تخفیف, مبلغ نهایی)"""
    total = sum(item.food.price * item.quantity for item in items)
    discount_amount = 0
    if discount:
        discount_amount = total * discount.percent // 100
    return total, discount_amount, total - discount_amount