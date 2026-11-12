from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext as _

from accounts.decorators import role_required
from accounts.models import User
from .forms import RestaurantForm, FoodForm
from .models import Restaurant, Food


# ---------- بخش عمومی (مشتری و مهمان) ----------

def restaurant_list(request):
    q = request.GET.get('q', '').strip()
    restaurants = Restaurant.objects.order_by('name')
    if q:
        restaurants = restaurants.filter(
            Q(name__icontains=q) | Q(foods__name__icontains=q)
        ).distinct()
    return render(request, 'restaurants/restaurant_list.html',
                  {'restaurants': restaurants, 'q': q})


def restaurant_detail(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    foods = restaurant.foods.all()
    return render(request, 'restaurants/restaurant_detail.html',
                  {'restaurant': restaurant, 'foods': foods})


# ---------- بخش صاحب رستوران ----------

@role_required(User.Role.OWNER)
def owner_dashboard(request):
    restaurants = request.user.restaurants.prefetch_related('foods')
    return render(request, 'restaurants/owner_dashboard.html',
                  {'restaurants': restaurants})


@role_required(User.Role.OWNER)
def restaurant_create(request):
    if request.method == 'POST':
        form = RestaurantForm(request.POST)
        if form.is_valid():
            restaurant = form.save(commit=False)
            restaurant.owner = request.user
            restaurant.save()
            messages.success(request, _('Restaurant created successfully.'))
            return redirect('restaurants:owner_dashboard')
    else:
        form = RestaurantForm()
    return render(request, 'restaurants/form.html',
                  {'form': form, 'title': _('New restaurant')})


@role_required(User.Role.OWNER)
def restaurant_edit(request, pk):
    # فقط رستوران خود کاربر؛ برای رستوران دیگران ۴۰۴ می‌دهد
    restaurant = get_object_or_404(Restaurant, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = RestaurantForm(request.POST, instance=restaurant)
        if form.is_valid():
            form.save()
            messages.success(request, _('Restaurant updated successfully.'))
            return redirect('restaurants:owner_dashboard')
    else:
        form = RestaurantForm(instance=restaurant)
    return render(request, 'restaurants/form.html',
                  {'form': form, 'title': _('Edit restaurant')})


@role_required(User.Role.OWNER)
def food_create(request, restaurant_pk):
    restaurant = get_object_or_404(Restaurant, pk=restaurant_pk, owner=request.user)
    if request.method == 'POST':
        form = FoodForm(request.POST, request.FILES)
        if form.is_valid():
            food = form.save(commit=False)
            food.restaurant = restaurant
            food.save()
            messages.success(request, _('Food added successfully.'))
            return redirect('restaurants:owner_dashboard')
    else:
        form = FoodForm()
    return render(request, 'restaurants/form.html',
                  {'form': form, 'title': _('New food')})


@role_required(User.Role.OWNER)
def food_edit(request, pk):
    food = get_object_or_404(Food, pk=pk, restaurant__owner=request.user)
    if request.method == 'POST':
        form = FoodForm(request.POST, request.FILES, instance=food)
        if form.is_valid():
            form.save()
            messages.success(request, _('Food updated successfully.'))
            return redirect('restaurants:owner_dashboard')
    else:
        form = FoodForm(instance=food)
    return render(request, 'restaurants/form.html',
                  {'form': form, 'title': _('Edit food')})


@role_required(User.Role.OWNER)
def food_delete(request, pk):
    food = get_object_or_404(Food, pk=pk, restaurant__owner=request.user)
    if request.method == 'POST':
        food.delete()
        messages.success(request, _('Food deleted successfully.'))
        return redirect('restaurants:owner_dashboard')
    return render(request, 'restaurants/food_confirm_delete.html', {'food': food})