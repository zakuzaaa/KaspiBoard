from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponseForbidden


from .models import Ad, Category, City, Favorite, Banner
from .forms import UserRegistrationForm, AdForm

def register_view(request):
    if request.user.is_authenticated: return redirect('ad_list')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Аккаунт создан! Теперь вы можете войти.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated: return redirect('profile')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('profile')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('ad_list')

# --- ПРОФИЛЬ ---

@login_required
def profile_view(request):
    my_ads = Ad.objects.filter(author=request.user).order_by('-created_at')
    favorites = Favorite.objects.filter(user=request.user).select_related('ad')
    return render(request, 'profile.html', {'my_ads': my_ads, 'favorites': favorites})

# --- ОБЪЯВЛЕНИЯ (КАТАЛОГ И ДЕТАЛИ) ---

def ad_list_view(request, slug=None):
    ads = Ad.objects.filter(is_moderated=True)
    if slug: ads = ads.filter(category__slug=slug)

    # Поиск
    q = request.GET.get('q')
    if q: ads = ads.filter(Q(title__icontains=q) | Q(description__icontains=q))

    # Сортировка
    sort = request.GET.get('sort')
    if sort == 'cheap': ads = ads.order_by('price', '-created_at')
    elif sort == 'expensive': ads = ads.order_by('-price', '-created_at')
    elif sort == 'free':
        ads = ads.filter(price=0).order_by('-created_at')
    else: ads = ads.order_by('-created_at')

    page_obj = Paginator(ads, 9).get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'banners': Banner.objects.filter(is_active=True),
        'current_slug': slug,
        'query_params': request.GET.copy().pop('page', True) and request.GET.urlencode(),
    }
    return render(request, 'ad_list.html', context)

def ad_detail_view(request, uuid):
    ad = get_object_or_404(Ad, uuid=uuid, is_moderated=True)
    is_favorite = request.user.is_authenticated and Favorite.objects.filter(user=request.user, ad=ad).exists()
    return render(request, 'ad_detail.html', {'ad': ad, 'is_favorite': is_favorite})


@login_required
def ad_create_view(request):
    if request.method == 'POST':
        form = AdForm(request.POST, request.FILES)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.author = request.user
            ad.is_moderated = False  
            ad.save()
            messages.success(request, 'Объявление отправлено на проверку.')
            return redirect('profile')
    else:
        form = AdForm()
    return render(request, 'ad_form.html', {'form': form})    

@login_required
def ad_update_view(request, uuid):
    ad = get_object_or_404(Ad, uuid=uuid)
    if ad.author != request.user: return HttpResponseForbidden('Доступ запрещен.')

    if request.method == 'POST':
        form = AdForm(request.POST, request.FILES, instance=ad)
        if form.is_valid():
            form.save()
            messages.success(request, 'Объявление обновлено.')
            return redirect('ad_detail', uuid=ad.uuid)
    else:
        form = AdForm(instance=ad)
    return render(request, 'ad_form.html', {'form': form,})   

@login_required
def ad_delete_view(request, uuid):
    ad = get_object_or_404(Ad, uuid=uuid)
    if ad.author != request.user: return HttpResponseForbidden('Доступ запрещен.')

    if request.method == 'POST':
        ad.delete()
        messages.success(request, 'Объявление удалено.')
        return redirect('profile')
    return render(request, 'ad_confirm_delete.html', {'ad': ad})

@login_required
def toggle_favorite(request, uuid):    
    ad = get_object_or_404(Ad, uuid=uuid)
    favorite, created = Favorite.objects.get_or_create(user=request.user, ad=ad)
    if not created: favorite.delete()
    return redirect(request.META.get('HTTP_REFERER', 'ad_list'))

from rest_framework import generics, permissions
from .serializers import AdSerializer

class AdListCreateAPIView(generics.ListCreateAPIView):
    queryset = Ad.objects.filter(is_moderated=True)
    serializer_class = AdSerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]        


from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.models import User
from .forms import ReviewForm

def leave_review(request, user_id):
    recipient = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.author = request.user
            review.recipient = recipient
            review.save()
    return redirect('profile_view', user_id=user_id) # Назад в профиль    