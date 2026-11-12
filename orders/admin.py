from django.contrib import admin

from .models import DiscountCode, Cart, CartItem, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'restaurant', 'status', 'final_price', 'created_at')
    list_filter = ('status', 'restaurant')
    inlines = [OrderItemInline]


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    inlines = [CartItemInline]


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'restaurant', 'percent', 'is_active', 'valid_from', 'valid_to')
    list_filter = ('is_active', 'restaurant')