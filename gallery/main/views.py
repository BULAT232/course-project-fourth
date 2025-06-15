from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import models
from django.utils.translation import gettext_lazy as _
from .forms import UserLoginForm, UserRegisterForm, UserProfileForm
from .models import User, Verification, Artwork, Order, Category, Review, Artist
from django.db.models import Count, Q 
from django.db.models import Avg, Count, Sum, Min, Max, Q, F, ExpressionWrapper, DurationField, Case, When
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .forms import AdminUserEditForm, AdminArtworkForm
from .filters import ArtworkAdminFilter
from django.core.paginator import Paginator
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .serializers import ArtworkSerializer, ArtistSerializer, CategorySerializer, ReviewSerializer, OrderSerializer
from django.http import HttpRequest, HttpResponse
from decimal import Decimal
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from typing import Optional, Any, Union

def is_admin(user: User) -> bool:
    """
    Проверяет, является ли пользователь администратором.
    
    Args:
        user: Объект пользователя для проверки
        
    Returns:
        True если пользователь является администратором или персоналом, иначе False
    """
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def home(request: HttpRequest) -> HttpResponse:
    """
    Отображает домашнюю страницу с категориями, избранными работами, отзывами и художниками.
    
    Args:
        request: HTTP-запрос
        
    Returns:
        Отрендеренный шаблон домашней страницы
    """
    # Получаем категории с количеством активных работ
    categories = Category.objects.annotate(
        num_artworks=Count('artworks', filter=Q(artworks__status='active'))
    ).all()[:4]

    # Избранные работы (3 последние активные)
    featured_artworks = Artwork.objects.filter(
        image__isnull=False
    ).exclude(image='')

    # Отзывы (3 последних одобренных)
    reviews = Review.objects.filter(is_approved=True).select_related(
        'order__buyer', 'artwork'
    ).order_by('-created_at')[:3]

    # Художники (первые 4)
    artists = Artist.objects.all()[:4]

    context = {
        'categories': categories,
        'featured_artworks': featured_artworks,
        'reviews': reviews,
        'artists': artists,
    }
    return render(request, 'home.html', context)

def register_view(request: HttpRequest) -> HttpResponse:
    """
    Обрабатывает регистрацию новых пользователей.
    
    Args:
        request: HTTP-запрос
        
    Returns:
        Редирект на профиль при успешной регистрации или форму регистрации
    """
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Если регистрируется продавец, создаем запись верификации
            if user.role == 'seller':
                Verification.objects.create(user=user)
                messages.info(request, _('Ваш аккаунт продавца ожидает верификации'))
            
            login(request, user)
            messages.success(request, _('Регистрация прошла успешно!'))
            return redirect('main:profile')
    else:
        form = UserRegisterForm()
    
    return render(request, 'register.html', {'form': form})

def login_view(request: HttpRequest) -> HttpResponse:
    """
    Обрабатывает аутентификацию пользователей.
    
    Args:
        request: HTTP-запрос
        
    Returns:
        Редирект на соответствующие страницы при успешной аутентификации или форму входа
    """
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # Проверяем, является ли пользователь администратором
                if user.is_staff or user.is_superuser:
                    return redirect('main:admin_dashboard')
                
                # Проверяем, является ли пользователь продавцом
                if user.role == 'seller':
                    # Проверяем статус верификации
                    try:
                        verification = Verification.objects.get(user=user)
                        if verification.status != 'verified':
                            messages.warning(request, _('Ваш аккаунт продавца ожидает верификации'))
                    except Verification.DoesNotExist:
                        messages.warning(request, _('Ваш аккаунт продавца не верифицирован'))
                
                return redirect('main:profile')
        else:
            messages.error(request, _('Неверный email/логин или пароль'))
    else:
        form = UserLoginForm()
    
    return render(request, 'login.html', {'form': form})

@login_required
def logout_view(request: HttpRequest) -> HttpResponse:
    """
    Обрабатывает выход пользователя из системы.
    
    Args:
        request: HTTP-запрос
        
    Returns:
        Редирект на домашнюю страницу
    """
    logout(request)
    messages.success(request, _('Вы успешно вышли из системы'))
    return redirect('main:home')

@login_required
@user_passes_test(is_admin, login_url='login')
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Отображает административную панель со статистикой и управлением.
    
    Args:
        request: HTTP-запрос
        
    Returns:
        Отрендеренный шаблон административной панели
    """
    # Статистика для администратора
    artworks = Artwork.objects.all()
    orders = Order.objects.all()
    users = User.objects.all()
    
    # Фильтрация картин
    artwork_filter = ArtworkAdminFilter(request.GET, queryset=artworks.order_by('-created_at'))
    filtered_artworks = artwork_filter.qs
    
    # Пагинация
    paginator = Paginator(filtered_artworks, 10)  # 10 картин на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получение строки запроса для пагинации
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    query_string = query_params.urlencode()
    
    context = {
        'total_artworks': artworks.count(),
        'total_orders': orders.count(),
        'total_users': users.count(),
        'recent_orders': orders.order_by('-created_at')[:5],
        'pending_verifications': Verification.objects.filter(status='pending').count(),
        'order_stats': orders.values('status').annotate(count=Count('id')),
        'filter': artwork_filter,
        'page_obj': page_obj,
        'query_string': query_string,
        'STATUS_CHOICES': Artwork.STATUS_CHOICES  # Добавляем статусы в контекст
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """
    Отображает и обновляет профиль пользователя.
    
    Args:
        request: HTTP-запрос
        
    Returns:
        Отрендеренный шаблон профиля пользователя
    """
    verification_status: Optional[str] = None
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Профиль успешно обновлен'))
            return redirect('main:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    # Проверка статуса верификации для продавцов
    if request.user.role == 'seller':
        try:
            verification = Verification.objects.get(user=request.user)
            verification_status = verification.status
        except Verification.DoesNotExist:
            verification_status = 'not_started'
    
    context = {
        'form': form,
        'verification_status': verification_status,
        'is_admin': request.user.is_staff or request.user.is_superuser
    }
    
    return render(request, 'profile.html', context)

@login_required
def add_to_cart(request: HttpRequest, artwork_id: int) -> HttpResponse:
    """
    Добавляет картину в корзину пользователя.
    
    Args:
        request: HTTP-запрос
        artwork_id: ID картины для добавления
        
    Returns:
        Редирект в корзину при успешном добавлении или на страницу картины при ошибке
    """
    try:
        artwork = Artwork.objects.get(id=artwork_id, status='active')
    except Artwork.DoesNotExist:
        messages.error(request, _('Картина не найдена или недоступна'))
        return redirect('main:home')
    
    # Проверка что пользователь не покупает свою картину
    if artwork.seller == request.user:
        messages.error(request, _('Вы не можете покупать свои собственные картины'))
        return redirect(artwork.get_absolute_url())
    
    # Проверка что картина еще не в корзине
    if Order.objects.filter(artwork=artwork, status='created').exists():
        messages.warning(request, _('Эта картина в единственном экземпляре и уже в чьей-то корзине'))
        return redirect(artwork.get_absolute_url())
    
    try:
        # Преобразуем цену к Decimal для безопасности
        price = Decimal(str(artwork.discounted_price))
    except (TypeError, InvalidOperation):
        price = artwork.price
    
    try:
        # Создание заказа
        Order.objects.create(
            buyer=request.user,
            artwork=artwork,
            price=price,
            status='created'
        )
        messages.success(request, _('Картина добавлена в корзину!'))
    except IntegrityError:
        messages.error(request, _('Не удалось добавить картину в корзину'))
    
    return redirect('main:cart_view')

def artwork_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Отображает детальную информацию о картине.
    
    Args:
        request: HTTP-запрос
        pk: ID картины
        
    Returns:
        Отрендеренный шаблон детальной страницы картины
    """
    artwork = get_object_or_404(Artwork, id=pk)
    context = {'artwork': artwork}
    return render(request, 'artwork_detail.html', context)

@login_required
def cart_view(request: HttpRequest) -> HttpResponse:
    """
    Отображает содержимое корзины пользователя.
    
    Args:
        request: HTTP-запрос
        
    Returns:
        Отрендеренный шаблон корзины
    """
    cart_items = Order.objects.filter(
        buyer=request.user, 
        status='created'
    ).select_related('artwork')
    
    total = sum(item.price for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total': total
    }
    return render(request, 'cart.html', context)

@login_required
def remove_from_cart(request: HttpRequest, order_id: int) -> HttpResponse:
    """
    Удаляет товар из корзины пользователя.
    
    Args:
        request: HTTP-запрос
        order_id: ID заказа для удаления
        
    Returns:
        Редирект в корзину после удаления
    """
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    order.delete()
    messages.success(request, _('Товар удален из корзины'))
    return redirect('main:cart_view')

@login_required
def checkout(request: HttpRequest) -> HttpResponse:
    """
    Промежуточная функция для оформления заказа (проверка доступности).
    
    Args:
        request: HTTP-запрос
        
    Returns:
        Редирект в корзину при наличии недоступных товаров
    """
    cart_items = Order.objects.filter(
        buyer=request.user, 
        status='created'
    )
    
    for item in cart_items:
        # Проверка что картина еще доступна
        if item.artwork.status != 'active':
            messages.error(request, 
                _('Картина "%s" больше не доступна для покупки') % item.artwork.title)
            return redirect('main:cart_view')
    return redirect('main:checkout_view')

@login_required
def checkout_view(request: HttpRequest) -> HttpResponse:
    """
    Отображает страницу оформления заказа и обрабатывает его подтверждение.
    
    Args:
        request: HTTP-запрос
        
    Returns:
        Отрендеренная страница оформления заказа или редирект на профиль после оформления
    """
    cart_items = Order.objects.filter(
        buyer=request.user, 
        status='created'
    )
    
    # Проверка доступности всех картин
    unavailable_items = []
    for item in cart_items:
        if item.artwork.status != 'active':
            unavailable_items.append(item)
    
    if unavailable_items:
        for item in unavailable_items:
            messages.error(request, 
                _('Картина "%s" больше не доступна для покупки') % item.artwork.title)
            item.delete()
        return redirect('main:cart_view')
    
    if not cart_items:
        messages.warning(request, _('Ваша корзина пуста'))
        return redirect('main:cart_view')
    
    total = sum(item.price for item in cart_items)
    
    # Проверка минимальной суммы заказа
    MIN_ORDER_AMOUNT = Decimal('15000.00')
    if total < MIN_ORDER_AMOUNT:
        messages.error(request, 
            _('Минимальная сумма заказа 15 000 ₽. Добавьте еще товаров в корзину.'))
        return redirect('main:cart_view')
    
    if request.method == 'POST':
        # Обработка оформления заказа
        for item in cart_items:
            item.complete_order()
        
        messages.success(request, _('Заказ успешно оформлен!'))
        return redirect('main:profile')
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'min_order_amount': MIN_ORDER_AMOUNT
    }
    return render(request, 'checkout.html', context)

@login_required
@user_passes_test(is_admin, login_url='login')
def admin_user_management(request: HttpRequest) -> HttpResponse:
    """
    Отображает страницу управления пользователями для администратора.
    
    Args:
        request: HTTP-запрос
        
    Returns:
        Отрендеренный шаблон управления пользователями
    """
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin_user_management.html', {'users': users})

@login_required
@user_passes_test(is_admin, login_url='login')
def admin_user_edit(request: HttpRequest, user_id: int) -> HttpResponse:
    """
    Редактирует данные пользователя (для администратора).
    
    Args:
        request: HTTP-запрос
        user_id: ID пользователя для редактирования
        
    Returns:
        Отрендеренная форма редактирования пользователя или редирект после сохранения
    """
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Пользователь успешно обновлен'))
            return redirect('main:admin_user_management')
    else:
        form = AdminUserEditForm(instance=user)
    
    return render(request, 'admin_user_edit.html', {'form': form, 'user': user})

@login_required
@user_passes_test(is_admin, login_url='login')
def admin_artwork_create(request: HttpRequest) -> HttpResponse:
    """
    Создает новую картину (для администратора).
    
    Args:
        request: HTTP-запрос
        
    Returns:
        Отрендеренная форма создания картины или редирект после сохранения
    """
    if request.method == 'POST':
        form = AdminArtworkForm(request.POST, request.FILES)
        if form.is_valid():
            artwork = form.save(commit=False)
            artwork.seller = request.user  # Админ выступает как продавец
            artwork.save()
            messages.success(request, _('Картина успешно добавлена'))
            return redirect('main:admin_dashboard')
    else:
        form = AdminArtworkForm()
    
    return render(request, 'admin_artwork_create.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def admin_user_create(request: HttpRequest) -> HttpResponse:
    """
    Создает нового пользователя (для суперпользователя).
    
    Args:
        request: HTTP-запрос
        
    Returns:
        Редирект на административную панель после создания пользователя
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'buyer')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, _('Пользователь с таким логином уже существует'))
            return redirect('main:admin_dashboard')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, _('Пользователь с таким email уже существует'))
            return redirect('main:admin_dashboard')
            
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            role=role
        )
        messages.success(request, _('Пользователь успешно создан'))
        return redirect('main:admin_dashboard')
    
    return redirect('main:admin_dashboard')

@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def admin_artwork_edit(request: HttpRequest, artwork_id: int) -> HttpResponse:
    """
    Редактирует данные картины (для суперпользователя).
    
    Args:
        request: HTTP-запрос
        artwork_id: ID картины для редактирования
        
    Returns:
        Отрендеренная форма редактирования картины или редирект после сохранения
    """
    artwork = get_object_or_404(Artwork, id=artwork_id)
    
    if request.method == 'POST':
        form = AdminArtworkForm(request.POST, request.FILES, instance=artwork)
        if form.is_valid():
            form.save()
            messages.success(request, _('Картина успешно обновлена'))
            return redirect('main:admin_dashboard')
    else:
        form = AdminArtworkForm(instance=artwork)
    
    return render(request, 'admin_artwork_edit.html', {
        'form': form,
        'artwork': artwork
    })

@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def admin_artwork_delete(request: HttpRequest, artwork_id: int) -> HttpResponse:
    """
    Удаляет картину (для суперпользователя).
    
    Args:
        request: HTTP-запрос
        artwork_id: ID картины для удаления
        
    Returns:
        Страница подтверждения удаления или редирект после удаления
    """
    artwork = get_object_or_404(Artwork, id=artwork_id)
    
    if request.method == 'POST':
        artwork.delete()
        messages.success(request, _('Картина успешно удалена'))
        return redirect('main:admin_dashboard')
    
    return render(request, 'admin_artwork_confirm_delete.html', {
        'artwork': artwork
    })

@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def admin_artwork_search(request: HttpRequest) -> HttpResponse:
    """
    Выполняет поиск картин по запросу (для суперпользователя).
    
    Args:
        request: HTTP-запрос
        
    Returns:
        Отрендеренная страница с результатами поиска
    """
    query = request.GET.get('q', '')
    
    if query:
        artworks = Artwork.objects.filter(
            Q(title__icontains=query) |
            Q(artist__name__icontains=query) |
            Q(description__icontains=query)
        )[:10]
    else:
        artworks = Artwork.objects.none()
    
    return render(request, 'admin_artwork_search.html', {
        'artworks': artworks,
        'query': query
    })

class ArtworkViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с картинами через API.
    Предоставляет CRUD операции для картин.
    """
    queryset = Artwork.objects.select_related(
        'artist', 'category', 'seller'
    ).prefetch_related('in_favorites')
    serializer_class = ArtworkSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_context(self) -> dict:
        """
        Добавляет request в контекст сериализатора.
        
        Returns:
            Словарь с контекстом для сериализатора
        """
        return {'request': self.request}

class ArtistViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с художниками через API.
    Предоставляет CRUD операции для художников.
    """
    queryset = Artist.objects.annotate(
        artworks_count=Count('artworks')
    ).all()
    serializer_class = ArtistSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с категориями через API.
    Предоставляет CRUD операции для категорий.
    """
    queryset = Category.objects.annotate(
        artworks_count=Count('artworks'),
        min_price=Min('artworks__price'),
        max_price=Max('artworks__price'),
        avg_price=Avg('artworks__price')
    ).all()
    serializer_class = CategorySerializer

class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с отзывами через API.
    Предоставляет CRUD операции для отзывов.
    """
    queryset = Review.objects.filter(is_approved=True).select_related(
        'order__buyer', 'artwork'
    )
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с заказами через API.
    Предоставляет CRUD операции для заказов.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Order.objects.all()  # Явно указываем базовый queryset
    
    def get_queryset(self) -> models.QuerySet:
        """
        Возвращает queryset заказов с учетом прав доступа пользователя.
        
        Returns:
            QuerySet заказов, доступных текущему пользователю
        """
        user = self.request.user
        queryset = super().get_queryset().select_related(
            'artwork', 'artwork__artist', 'buyer'
        ).annotate(
            days_since_created=ExpressionWrapper(
                timezone.now() - F('created_at'),
                output_field=DurationField()
            )
        )
        
        if user.is_staff:
            return queryset
        return queryset.filter(buyer=user)
    
    def perform_create(self, serializer: OrderSerializer) -> None:
        """
        Сохраняет заказ с указанием покупателя.
        
        Args:
            serializer: Сериализатор заказа
        """
        serializer.save(buyer=self.request.user)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

class CustomAuthToken(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Please provide both username and password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        
        if not user:
            return Response(
                {'error': 'Invalid Credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })