from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import User
from restaurants.models import Food
from .forms import CheckoutForm, DiscountCodeForm
from .models import Cart, CartItem, DiscountCode, Order, OrderItem
from .utils import (FINAL_STATUSES, allowed_next_statuses,
                    calculate_prices, validate_discount)


# ====================== سبد خرید (نمودار ۱) ======================

@require_POST
@role_required(User.Role.CUSTOMER)
def add_to_cart(request, food_id):
    food = get_object_or_404(Food.objects.select_related('restaurant'), pk=food_id)

    if not food.is_available:
        messages.error(request, _('This food is not available.'))
        return redirect('restaurants:detail', pk=food.restaurant_id)

    cart, _created = Cart.objects.get_or_create(user=request.user)

    if cart.items.exclude(food__restaurant=food.restaurant).exists():
        if request.POST.get('confirm_clear') != '1':
            current = cart.items.select_related('food__restaurant').first().food.restaurant
            return render(request, 'orders/cart_conflict.html',
                          {'food': food, 'current_restaurant': current})
        cart.items.all().delete()

    item, created = CartItem.objects.get_or_create(cart=cart, food=food)
    if not created:
        item.quantity += 1
        item.save()

    messages.success(request, _('Food added to your cart.'))
    return redirect('orders:cart')


def _cart_context(request):
    """اطلاعات صفحه‌ی سبد: آیتم‌ها، رستوران، کد تخفیف معتبر و قیمت‌ها"""
    cart, _created = Cart.objects.get_or_create(user=request.user)
    items = list(cart.items.select_related('food', 'food__restaurant'))
    for item in items:
        item.line_total = item.food.price * item.quantity
    restaurant = items[0].food.restaurant if items else None

    discount = None
    code_id = request.session.get('discount_code_id')
    if code_id:
        saved = DiscountCode.objects.filter(pk=code_id).first()
        if saved and restaurant:
            discount, _error = validate_discount(saved.code, restaurant)
        if not discount:
            request.session.pop('discount_code_id', None)
            if items:
                messages.warning(
                    request, _('Your discount code is no longer valid and was removed.'))

    total, discount_amount, final_price = calculate_prices(items, discount)
    return {'cart': cart, 'items': items, 'restaurant': restaurant,
            'discount': discount, 'total': total,
            'discount_amount': discount_amount, 'final_price': final_price}


@role_required(User.Role.CUSTOMER)
def cart_detail(request):
    ctx = _cart_context(request)
    ctx['form'] = CheckoutForm(initial={'delivery_address': request.user.address})
    return render(request, 'orders/cart.html', ctx)


@require_POST
@role_required(User.Role.CUSTOMER)
def cart_item_update(request, pk):
    item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    action = request.POST.get('action')
    if action == 'inc':
        item.quantity += 1
        item.save()
    elif action == 'dec':
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
    return redirect('orders:cart')


@require_POST
@role_required(User.Role.CUSTOMER)
def cart_item_remove(request, pk):
    item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    item.delete()
    return redirect('orders:cart')


# ====================== کد تخفیف: سمت مشتری (نمودار ۲، بخش ب) ======================

@require_POST
@role_required(User.Role.CUSTOMER)
def apply_discount(request):
    cart, _created = Cart.objects.get_or_create(user=request.user)
    first = cart.items.select_related('food__restaurant').first()
    if first is None:
        messages.error(request, _('Your cart is empty.'))
        return redirect('orders:cart')

    discount, error = validate_discount(request.POST.get('code'), first.food.restaurant)
    if error:
        messages.error(request, error)
    else:
        request.session['discount_code_id'] = discount.pk
        messages.success(request, _('Discount code applied.'))
    return redirect('orders:cart')


@require_POST
@role_required(User.Role.CUSTOMER)
def remove_discount(request):
    request.session.pop('discount_code_id', None)
    messages.success(request, _('Discount code removed.'))
    return redirect('orders:cart')


# ====================== ثبت سفارش (نمودار ۳) ======================

@require_POST
@role_required(User.Role.CUSTOMER)
def place_order(request):
    cart, _created = Cart.objects.get_or_create(user=request.user)
    items = list(cart.items.select_related('food', 'food__restaurant'))

    # ۱) سبد خالی؟
    if not items:
        messages.error(request, _('Your cart is empty.'))
        return redirect('orders:cart')

    restaurants = {item.food.restaurant_id for item in items}
    if len(restaurants) > 1:
        messages.error(request, _('Your cart contains foods from more than one restaurant.'))
        return redirect('orders:cart')
    restaurant = items[0].food.restaurant

    # ۲) آدرس تحویل
    form = CheckoutForm(request.POST)
    if not form.is_valid():
        ctx = _cart_context(request)
        ctx['form'] = form
        return render(request, 'orders/cart.html', ctx)

    # ۳) همه‌ی غذاها هنوز در دسترس‌اند؟
    unavailable = [item for item in items if not item.food.is_available]
    if unavailable:
        for item in unavailable:
            item.delete()
        messages.error(request, _('Some foods are no longer available and were removed from your cart.'))
        return redirect('orders:cart')

    # ۴) اعتبارسنجی مجدد کد تخفیف در لحظه‌ی ثبت
    discount = None
    code_id = request.session.get('discount_code_id')
    if code_id:
        saved = DiscountCode.objects.filter(pk=code_id).first()
        error = None
        if saved:
            discount, error = validate_discount(saved.code, restaurant)
        if not discount:
            request.session.pop('discount_code_id', None)
            messages.error(request, _('The discount code is no longer valid. Please review your cart.'))
            return redirect('orders:cart')

    # ۵) تراکنش اتمیک: یا همه‌چیز انجام می‌شود یا هیچ‌چیز
    total, _discount_amount, final_price = calculate_prices(items, discount)
    with transaction.atomic():
        order = Order.objects.create(
            user=request.user,
            restaurant=restaurant,
            discount_code=discount,
            status=Order.Status.PREPARING,
            delivery_address=form.cleaned_data['delivery_address'],
            total_price=total,
            final_price=final_price,
        )
        OrderItem.objects.bulk_create([
            OrderItem(order=order, food=item.food, food_name=item.food.name,
                      price=item.food.price, quantity=item.quantity)
            for item in items
        ])
        cart.items.all().delete()

    request.session.pop('discount_code_id', None)
    messages.success(request, _('Order placed successfully.'))
    return redirect('orders:order_detail', pk=order.pk)


# ====================== سفارش‌ها: سمت مشتری (نمودار ۵) ======================

def _order_totals(order):
    items = list(order.items.all())
    for item in items:
        item.line_total = item.price * item.quantity
    return items, order.total_price - order.final_price


@role_required(User.Role.CUSTOMER)
def order_list(request):
    orders = request.user.orders.select_related('restaurant').order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})


@role_required(User.Role.CUSTOMER)
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('restaurant', 'discount_code'), pk=pk)
    if order.user_id != request.user.id:
        raise PermissionDenied
    items, discount_amount = _order_totals(order)
    return render(request, 'orders/order_detail.html', {
        'order': order, 'items': items, 'discount_amount': discount_amount,
        'can_cancel': order.status == Order.Status.PREPARING,
    })


@require_POST
@role_required(User.Role.CUSTOMER)
def order_cancel(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.user_id != request.user.id:
        raise PermissionDenied
    if order.status != Order.Status.PREPARING:
        messages.error(request, _('This order can no longer be canceled.'))
    else:
        order.status = Order.Status.CANCELED
        order.save(update_fields=['status'])
        messages.success(request, _('Order canceled.'))
    return redirect('orders:order_detail', pk=order.pk)


# ====================== سفارش‌ها: سمت صاحب رستوران (نمودار ۴) ======================

@role_required(User.Role.OWNER)
def owner_order_list(request):
    orders = (Order.objects.filter(restaurant__owner=request.user)
              .select_related('user', 'restaurant').order_by('-created_at'))
    status = request.GET.get('status', '')
    if status in Order.Status.values:
        orders = orders.filter(status=status)
    return render(request, 'orders/owner_order_list.html', {
        'orders': orders, 'status': status, 'statuses': Order.Status.choices})


@role_required(User.Role.OWNER)
def owner_order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('user', 'restaurant', 'discount_code'), pk=pk)
    if order.restaurant.owner_id != request.user.id:
        raise PermissionDenied
    items, discount_amount = _order_totals(order)
    next_statuses = [(s, Order.Status(s).label) for s in allowed_next_statuses(order)]
    return render(request, 'orders/owner_order_detail.html', {
        'order': order, 'items': items, 'discount_amount': discount_amount,
        'next_statuses': next_statuses})


@require_POST
@role_required(User.Role.OWNER)
def owner_order_set_status(request, pk):
    order = get_object_or_404(Order.objects.select_related('restaurant'), pk=pk)

    # تصمیم ۱: سفارش متعلق به رستوران این کاربر است؟
    if order.restaurant.owner_id != request.user.id:
        raise PermissionDenied

    new_status = request.POST.get('status')
    if order.status in FINAL_STATUSES:                         # تصمیم ۲
        messages.error(request, _('This order is closed and cannot be changed.'))
    elif new_status not in allowed_next_statuses(order):       # تصمیم ۳
        messages.error(request, _('Invalid status change.'))
    else:
        order.status = new_status
        order.save(update_fields=['status'])
        messages.success(request, _('Order status updated.'))
    return redirect('orders:owner_order_detail', pk=order.pk)


# ====================== کد تخفیف: سمت صاحب رستوران (نمودار ۲، بخش الف) ======================

@role_required(User.Role.OWNER)
def discount_list(request):
    codes = (DiscountCode.objects.filter(restaurant__owner=request.user)
             .select_related('restaurant').order_by('-valid_to'))
    return render(request, 'orders/discount_list.html', {'codes': codes})


@role_required(User.Role.OWNER)
def discount_create(request):
    form = DiscountCodeForm(request.POST or None, owner=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, _('Discount code created successfully.'))
        return redirect('orders:discount_list')
    return render(request, 'orders/form.html',
                  {'form': form, 'title': _('New discount code')})


@role_required(User.Role.OWNER)
def discount_edit(request, pk):
    code = get_object_or_404(DiscountCode, pk=pk, restaurant__owner=request.user)
    form = DiscountCodeForm(request.POST or None, instance=code, owner=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, _('Discount code updated successfully.'))
        return redirect('orders:discount_list')
    return render(request, 'orders/form.html',
                  {'form': form, 'title': _('Edit discount code')})