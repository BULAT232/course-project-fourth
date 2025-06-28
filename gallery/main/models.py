from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db.models import Avg
from django.core.exceptions import ValidationError
from django.db.models import Count, Q 

def validate_year(value):
    if value < 1000 or value > timezone.now().year:
        raise ValidationError(_('Некорректный год создания'))

class ActiveArtworkManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status='active')
    
    def with_discount(self):
        return self.filter(
            created_at__lt=timezone.now() - timezone.timedelta(days=30)
        )

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Email обязателен'))
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('buyer', _('Покупатель')),
        ('seller', _('Продавец')),
        ('moderator', _('Модератор')),
        ('admin', _('Администратор')),
    ]

    social_id = models.CharField(
        _('ID социального аккаунта'),
        max_length=255,
        blank=True,
        null=True
    )
    
    email = models.EmailField(_('Email'), unique=True)
    username = models.CharField(_('Логин'), max_length=30, unique=True)
    first_name = models.CharField(_('Имя'), max_length=30, blank=True)
    last_name = models.CharField(_('Фамилия'), max_length=30, blank=True)
    role = models.CharField(
        _('Роль'), 
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='buyer'
    )
    balance = models.DecimalField(
        _('Баланс'), 
        max_digits=10, 
        decimal_places=2, 
        default=0.00
    )
    rating = models.DecimalField(
        _('Рейтинг'), 
        max_digits=3, 
        decimal_places=2, 
        default=5.00,
        validators=[MinValueValidator(1.00), MaxValueValidator(5.00)]
    )
    date_joined = models.DateTimeField(_('Дата регистрации'), default=timezone.now)
    is_active = models.BooleanField(_('Активен'), default=True)
    is_staff = models.BooleanField(_('Персонал'), default=False)
    avatar = models.ImageField(
        _('Аватар'),
        upload_to='users/avatars/',
        blank=True,
        null=True
    )
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.username or self.email.split('@')[0]
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name or self.username
    
    def update_rating(self):
        reviews = self.reviews_received.all()
        if reviews.exists():
            avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
            self.rating = round(avg_rating, 2)
            self.save()

class Artist(models.Model):
    name = models.CharField(_('Имя художника'), max_length=100, unique=True)
    bio = models.TextField(_('Биография'), blank=True, null=True)
    photo = models.ImageField(
        _('Фотография'), 
        upload_to='artists/photos/',
        blank=True, 
        null=True
    )
    official_site = models.URLField(
        _('Официальный сайт'), 
        blank=True, 
        null=True
    )
    birth_date = models.DateField(_('Дата рождения'), blank=True, null=True)
    death_date = models.DateField(_('Дата смерти'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Художник')
        verbose_name_plural = _('Художники')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def age(self):
        if self.birth_date:
            today = timezone.now().date()
            born = self.birth_date
            return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        return None
    
    @property
    def is_alive(self):
        return self.death_date is None

class Category(models.Model):
    name = models.CharField(_('Название категории'), max_length=100, unique=True)
    description = models.TextField(_('Описание'), blank=True, null=True)
    icon = models.CharField(_('Иконка'), max_length=50, blank=True, null=True)
    
    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Artwork(models.Model):
    STATUS_CHOICES = [
        ('active', _('Активен')),
        ('sold', _('Продан')),
        ('reserved', _('Зарезервирован')),
        ('archived', _('В архиве')),
    ]
    
    STYLE_CHOICES = [
        ('realism', _('Реализм')),
        ('abstract', _('Абстракционизм')),
        ('impressionism', _('Импрессионизм')),
        ('surrealism', _('Сюрреализм')),
        ('pop_art', _('Поп-арт')),
        ('cubism', _('Кубизм')),
        ('expressionism', _('Экспрессионизм')),
        ('renaissance', _('Ренессанс')),
        ('baroque', _('Барокко')),
        ('romanticism', _('Романтизм')),
    ]
    
    MEDIUM_CHOICES = [
        ('oil', _('Масло')),
        ('acrylic', _('Акрил')),
        ('watercolor', _('Акварель')),
        ('pastel', _('Пастель')),
        ('digital', _('Цифровое искусство')),
        ('charcoal', _('Уголь')),
        ('ink', _('Тушь')),
        ('pencil', _('Карандаш')),
        ('mixed', _('Смешанная техника')),
    ]
    
    objects = models.Manager()
    active = ActiveArtworkManager()  # Убедитесь, что менеджер корректно определен
    
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='artworks',
        verbose_name=_('Продавец')
    )
    artist = models.ForeignKey(
        Artist,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='artworks',
        verbose_name=_('Художник')
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='artworks',
        verbose_name=_('Категория')
    )
    title = models.CharField(_('Название'), max_length=120)
    description = models.TextField(_('Описание'))
    image = models.ImageField(
        _('Изображение'), 
        upload_to='artworks/images/%Y/%m/%d/'
    )
    style = models.CharField(
        _('Стиль'), 
        max_length=50, 
        choices=STYLE_CHOICES
    )
    medium = models.CharField(
        _('Техника'), 
        max_length=50, 
        choices=MEDIUM_CHOICES
    )
    year_created = models.IntegerField(
        _('Год создания'),
        validators=[MinValueValidator(1000)]
    )
    width = models.DecimalField(
        _('Ширина (см)'), 
        max_digits=6, 
        decimal_places=1,
        validators=[MinValueValidator(1)]
    )
    height = models.DecimalField(
        _('Высота (см)'), 
        max_digits=6, 
        decimal_places=1,
        validators=[MinValueValidator(1)]
    )
    depth = models.DecimalField(
        _('Глубина (см)'), 
        max_digits=6, 
        decimal_places=1,
        blank=True,
        null=True,
        help_text=_('Только для скульптур и 3D работ')
    )
    price = models.DecimalField(
        _('Цена'), 
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    status = models.CharField(
        _('Статус'), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active'
    )
    is_framed = models.BooleanField(_('В рамке'), default=False)
    is_certified = models.BooleanField(_('Сертификат подлинности'), default=False)
    created_at = models.DateTimeField(
        _('Дата добавления'), 
        auto_now_add=True,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Картина')
        verbose_name_plural = _('Картины')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['price']),
            models.Index(fields=['created_at']),
        ]
    
    # Убрали кастомный save, так как auto_now_add=True достаточно
    
    @property
    def has_discount(self):
        if not self.created_at:
            return False
        days = (timezone.now() - self.created_at).days
        return days > 30

    @property
    def discounted_price(self):
        if not self.created_at:
            return self.price
        days = (timezone.now() - self.created_at).days
        if days > 180:
            return self.price * Decimal('0.7')
        elif days > 90:
            return self.price * Decimal('0.8')
        elif days > 30:
            return self.price * Decimal('0.9')
        return self.price

    @property
    def discount_percentage(self):
        if not self.created_at:
            return Decimal('0')
        days = (timezone.now() - self.created_at).days
        if days > 180:
            return Decimal('0.3')
        elif days > 90:
            return Decimal('0.2')
        elif days > 30:
            return Decimal('0.1')
        return Decimal('0')
    
    def __str__(self):
        artist_name = self.artist.name if self.artist else 'Неизвестный художник'
        return f"{self.title} ({artist_name})"
    
    def get_absolute_url(self):
        return reverse('main:artwork_detail', kwargs={'pk': self.pk})
    
    def dimensions(self):
        if self.depth:
            return f"{self.width} × {self.height} × {self.depth} см"
        return f"{self.width} × {self.height} см"
    
    def discount_status(self):
        if not self.created_at:
            return _("Без скидки")
        days = (timezone.now() - self.created_at).days
        if days > 180:
            return _("Скидка 30%")
        elif days > 90:
            return _("Скидка 20%")
        elif days > 30:
            return _("Скидка 10%")
        return _("Без скидки")
    
    def calculate_discount_price(self):
        if not self.created_at:
            return self.price
        days = (timezone.now() - self.created_at).days
        if days > 180:
            return self.price * Decimal('0.7')
        elif days > 90:
            return self.price * Decimal('0.8')
        elif days > 30:
            return self.price * Decimal('0.9')
        return self.price

    def clean(self):
        # Пропускаем проверку для новых объектов
        if not self.pk:
            return
            
        if self.status == 'active' and self.orders.filter(status='created').exists():
            raise ValidationError(_('Эта картина уже находится в корзине у покупателя'))
class Order(models.Model):
    STATUS_CHOICES = [
        ('created', _('Создан')),
        ('paid', _('Оплачен')),
        ('shipped', _('Отправлен')),
        ('delivered', _('Доставлен')),
        ('completed', _('Завершен')),
        ('disputed', _('Спор')),
        ('cancelled', _('Отменен')),
    ]
    
    SHIPPING_METHODS = [
        ('pickup', _('Самовывоз')),
        ('courier', _('Курьер')),
        ('post', _('Почта')),
        ('express', _('Экспресс-доставка')),
    ]
    
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('Покупатель')
    )
    artwork = models.ForeignKey(
        Artwork,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('Картина')
    )
    price = models.DecimalField(
        _('Цена'), 
        max_digits=10, 
        decimal_places=2
    )
    status = models.CharField(
        _('Статус'), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='created'
    )
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    shipping_address = models.TextField(_('Адрес доставки'), blank=True, null=True)
    shipping_method = models.CharField(
        _('Способ доставки'), 
        max_length=20, 
        choices=SHIPPING_METHODS, 
        default='pickup'
    )
    shipping_cost = models.DecimalField(
        _('Стоимость доставки'), 
        max_digits=10, 
        decimal_places=2,
        default=0.00
    )
    insurance = models.BooleanField(_('Страховка'), default=False)
    insurance_cost = models.DecimalField(
        _('Стоимость страховки'), 
        max_digits=10, 
        decimal_places=2,
        default=0.00
    )
    total_price = models.DecimalField(
        _('Итоговая цена'), 
        max_digits=10, 
        decimal_places=2,
        editable=False
    )
    
    class Meta:
        verbose_name = _('Заказ')
        verbose_name_plural = _('Заказы')
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['artwork'],
                condition=Q(status='created'),
                name='unique_artwork_in_cart'
            )
        ]
    
    def __str__(self):
        return f"Заказ #{self.id} - {self.artwork.title}"
    
    def save(self, *args, **kwargs):
        self.price = Decimal(str(self.price)) if self.price else Decimal('0')
        self.shipping_cost = Decimal(str(self.shipping_cost)) if self.shipping_cost else Decimal('0')
        self.insurance_cost = Decimal(str(self.insurance_cost)) if self.insurance_cost else Decimal('0')
        
        self.total_price = self.price + self.shipping_cost + self.insurance_cost
        super().save(*args, **kwargs)
    
    def complete_order(self):
        """Завершение заказа и обновление статуса картины"""
        self.status = 'paid'
        self.save()
        self.artwork.status = 'sold'
        self.artwork.save()
    
    def payment_expired(self):
        return (timezone.now() - self.created_at) > timezone.timedelta(hours=48)

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Ожидает')),
        ('completed', _('Завершен')),
        ('refunded', _('Возвращен')),
        ('failed', _('Неудачный')),
    ]
    
    PAYMENT_METHODS = [
        ('card', _('Кредитная карта')),
        ('paypal', 'PayPal'),
        ('bank', _('Банковский перевод')),
        ('crypto', _('Криптовалюта')),
    ]
    
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name=_('Заказ')
    )
    amount = models.DecimalField(
        _('Сумма'), 
        max_digits=10, 
        decimal_places=2
    )
    method = models.CharField(
        _('Метод оплаты'), 
        max_length=50, 
        choices=PAYMENT_METHODS
    )
    transaction_id = models.CharField(
        _('ID транзакции'), 
        max_length=255, 
        unique=True
    )
    status = models.CharField(
        _('Статус'), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    completed_at = models.DateTimeField(_('Дата завершения'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Платеж')
        verbose_name_plural = _('Платежи')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Платеж #{self.id} для заказа #{self.order.id}"
    
    def mark_as_completed(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

class Review(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name=_('Заказ')
    )
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_received',
        verbose_name=_('Продавец')
    )
    artwork = models.ForeignKey(
        Artwork,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('Картина')
    )
    rating = models.PositiveSmallIntegerField(
        _('Рейтинг'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(_('Комментарий'), blank=True, null=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    is_approved = models.BooleanField(_('Одобрен'), default=False)
    
    class Meta:
        verbose_name = _('Отзыв')
        verbose_name_plural = _('Отзывы')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Отзыв к заказу #{self.order.id}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.seller.update_rating()

class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name=_('Пользователь')
    )
    artwork = models.ForeignKey(
        Artwork,
        on_delete=models.CASCADE,
        related_name='in_favorites',
        verbose_name=_('Картина')
    )
    added_at = models.DateTimeField(_('Добавлено'), auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'artwork')
        verbose_name = _('Избранное')
        verbose_name_plural = _('Избранные')
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.user} → {self.artwork.title}"

class ArtworkImage(models.Model):
    artwork = models.ForeignKey(
        Artwork,
        on_delete=models.CASCADE,
        related_name='additional_images',
        verbose_name=_('Картина')
    )
    image = models.ImageField(
        _('Дополнительное изображение'),
        upload_to='artworks/images/additional/%Y/%m/%d/'
    )
    description = models.CharField(
        _('Описание изображения'),
        max_length=255,
        blank=True,
        null=True
    )
    uploaded_at = models.DateTimeField(_('Дата загрузки'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Дополнительное изображение')
        verbose_name_plural = _('Дополнительные изображения')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Изображение для {self.artwork.title}"

class Verification(models.Model):
    STATUS_CHOICES = [
        ('pending', _('На проверке')),
        ('verified', _('Подтверждено')),
        ('rejected', _('Отклонено')),
    ]
    
    DOCUMENT_TYPES = [
        ('passport', _('Паспорт')),
        ('driver_license', _('Водительское удостоверение')),
        ('id_card', _('ID-карта')),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='verification',
        verbose_name=_('Пользователь')
    )
    document_type = models.CharField(
        _('Тип документа'), 
        max_length=50, 
        choices=DOCUMENT_TYPES
    )
    document_number = models.CharField(_('Номер документа'), max_length=100)
    document_front = models.ImageField(
        _('Лицевая сторона документа'),
        upload_to='verifications/documents/%Y/%m/%d/'
    )
    document_back = models.ImageField(
        _('Обратная сторона документа'),
        upload_to='verifications/documents/%Y/%m/%d/',
        blank=True,
        null=True
    )
    status = models.CharField(
        _('Статус'), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_users',
        verbose_name=_('Проверил')
    )
    verified_at = models.DateTimeField(_('Дата проверки'), blank=True, null=True)
    comment = models.TextField(_('Комментарий модератора'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Верификация')
        verbose_name_plural = _('Верификации')
        ordering = ['-verified_at']
    
    def __str__(self):
        return f"Верификация {self.user.username}"
    
    def verification_age(self):
        if self.verified_at:
            return (timezone.now() - self.verified_at).days
        return None
    
    def is_verification_active(self):
        age = self.verification_age()
        return age is not None and age < 365
    
    