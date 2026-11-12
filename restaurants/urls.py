from django.urls import path

from . import views

app_name = 'restaurants'

urlpatterns = [
    path('<int:pk>/', views.restaurant_detail, name='detail'),
    path('owner/', views.owner_dashboard, name='owner_dashboard'),
    path('owner/new/', views.restaurant_create, name='restaurant_create'),
    path('owner/<int:pk>/edit/', views.restaurant_edit, name='restaurant_edit'),
    path('owner/<int:restaurant_pk>/foods/new/', views.food_create, name='food_create'),
    path('owner/foods/<int:pk>/edit/', views.food_edit, name='food_edit'),
    path('owner/foods/<int:pk>/delete/', views.food_delete, name='food_delete'),
]