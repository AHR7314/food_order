from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import User
from restaurants.models import Food
from .models import Cart, CartItem


@require_POST
@role_required(User.Role.CUSTOMER)
def add_to_cart(request, food_id):
    food = get_object_or_404(Food.objects.select_related('restaurant'), pk=food_id)

    # ۱) غذا باید در دسترس باشد
    if not food.is_available:
        messages.error(request, _('This food is not available.'))
        return redirect('restaurants:detail', pk=food.restaurant_id)

    cart, _created = Cart.objects.get_or_create(user=request.user)

    # ۲) قانون یک سبد = یک رستوران
    if cart.items.exclude(food__restaurant=food.restaurant).exists():
        if request.POST.get('confirm_clear') != '1':
            current = cart.items.select_related('food__restaurant').first().food.restaurant
            return render(request, 'orders/cart_conflict.html',
                          {'food': food, 'current_restaurant': current})
        cart.items.all().delete()  # مشتری تایید کرد: سبد قبلی خالی می‌شود

    # ۳) افزایش تعداد یا ساخت آیتم جدید
    item, created = CartItem.objects.get_or_create(cart=cart, food=food)
    if not created:
        item.quantity += 1
        item.save()

    messages.success(request, _('Food added to your cart.'))
    return redirect('orders:cart')


@role_required(User.Role.CUSTOMER)
def cart_detail(request):
    cart, _created = Cart.objects.get_or_create(user=request.user)
    items = list(cart.items.select_related('food', 'food__restaurant'))

    total = 0
    for item in items:
        item.line_total = item.food.price * item.quantity
        total += item.line_total

    restaurant = items[0].food.restaurant if items else None
    return render(request, 'orders/cart.html',
                  {'items': items, 'total': total, 'restaurant': restaurant})


@require_POST
@role_required(User.Role.CUSTOMER)
def cart_item_update(request, pk):
    # فقط آیتم‌های سبد خود کاربر
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