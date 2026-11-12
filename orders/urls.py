from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_detail, name='cart'),
    path('cart/add/<int:food_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/item/<int:pk>/update/', views.cart_item_update, name='cart_item_update'),
    path('cart/item/<int:pk>/remove/', views.cart_item_remove, name='cart_item_remove'),
]