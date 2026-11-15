from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    # سبد و ثبت سفارش
    path('cart/', views.cart_detail, name='cart'),
    path('cart/add/<int:food_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/item/<int:pk>/update/', views.cart_item_update, name='cart_item_update'),
    path('cart/item/<int:pk>/remove/', views.cart_item_remove, name='cart_item_remove'),
    path('cart/discount/apply/', views.apply_discount, name='apply_discount'),
    path('cart/discount/remove/', views.remove_discount, name='remove_discount'),
    path('checkout/', views.place_order, name='place_order'),

    # سفارش‌های مشتری
    path('my/', views.order_list, name='order_list'),
    path('my/<int:pk>/', views.order_detail, name='order_detail'),
    path('my/<int:pk>/cancel/', views.order_cancel, name='order_cancel'),

    # سفارش‌ها و کد تخفیف صاحب رستوران
    path('owner/', views.owner_order_list, name='owner_order_list'),
    path('owner/<int:pk>/', views.owner_order_detail, name='owner_order_detail'),
    path('owner/<int:pk>/status/', views.owner_order_set_status, name='owner_order_set_status'),
    path('owner/discounts/', views.discount_list, name='discount_list'),
    path('owner/discounts/new/', views.discount_create, name='discount_create'),
    path('owner/discounts/<int:pk>/edit/', views.discount_edit, name='discount_edit'),
]