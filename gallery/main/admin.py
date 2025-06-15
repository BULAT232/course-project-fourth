from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Artist, Category, Artwork, 
    Order, Payment, Review, Favorite,
    ArtworkImage, Verification
)
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 
                    'balance', 'rating', 'date_joined', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Личная информация'), {'fields': ('username', 'first_name', 'last_name', 'avatar')}),
        (_('Роли и разрешения'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 
                       'groups', 'user_permissions'),
        }),
        (_('Финансы и рейтинг'), {'fields': ('balance', 'rating')}),
        (_('Важные даты'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    readonly_fields = ('last_login', 'date_joined')

class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'birth_date', 'death_date', 'is_alive', 'age')
    search_fields = ('name',)
    # Убрали фильтр по is_alive, так как это свойство, а не поле
    readonly_fields = ('age', 'is_alive')
    fieldsets = (
        (None, {'fields': ('name',)}),
        (_('Биография'), {'fields': ('bio', 'official_site')}),
        (_('Фотография'), {'fields': ('photo',)}),
        (_('Даты жизни'), {'fields': ('birth_date', 'death_date', 'age', 'is_alive')}),
    )

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    # Убрали prepopulated_fields, так как в модели нет slug
    # Если нужно, добавьте поле slug в модель Category

from django.contrib import admin
from .models import Artwork, ArtworkImage
from django.utils.translation import gettext_lazy as _

from django.contrib import admin
from .models import Artwork, ArtworkImage
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.http import HttpResponseRedirect

from django.contrib import admin
from .models import Artwork, ArtworkImage
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.http import HttpResponseRedirect

class ArtworkImageInline(admin.TabularInline):
    model = ArtworkImage
    extra = 1
    fields = ('image', 'description')
    verbose_name = _('Дополнительное изображение')
    verbose_name_plural = _('Дополнительные изображения')

    def has_add_permission(self, request, obj=None):
        # Разрешаем добавление изображений только при редактировании существующего объекта
        return obj is not None

class ArtworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'category', 'price', 'status', 
                    'created_at', 'seller')
    list_filter = ('status', 'category', 'style', 'medium', 'is_framed', 'is_certified')
    search_fields = ('title', 'description', 'artist__name')
    
    # Убрали discount_status из list_display, так как он может вызывать ошибку при создании
    inlines = [ArtworkImageInline]
    
    # Поля для формы создания
    add_fieldsets = (
        (None, {'fields': ('seller', 'title', 'description', 'status')}),
        (_('Художественные детали'), {
            'fields': ('artist', 'category', 'style', 'medium', 'year_created')
        }),
        (_('Физические характеристики'), {
            'fields': ('width', 'height', 'depth', 'is_framed', 'is_certified')
        }),
        (_('Финансы'), {
            'fields': ('price',)
        }),
        (_('Изображение'), {'fields': ('image',)}),
    )
    
    # Поля для формы редактирования
    edit_fieldsets = (
        (None, {'fields': ('seller', 'title', 'description', 'status')}),
        (_('Художественные детали'), {
            'fields': ('artist', 'category', 'style', 'medium', 'year_created')
        }),
        (_('Физические характеристики'), {
            'fields': ('width', 'height', 'depth', 'is_framed', 'is_certified')
        }),
        (_('Финансы'), {
            'fields': ('price',)
        }),
        (_('Изображение'), {'fields': ('image',)}),
    )
    
    actions = ['mark_as_sold', 'apply_discount']
    
    def get_fieldsets(self, request, obj=None):
        if obj:
            return self.edit_fieldsets
        return self.add_fieldsets
    
    def get_readonly_fields(self, request, obj=None):
        # Убрали discount_status, так как он требует первичного ключа
        if obj:
            return ['created_at']  # Только неизменяемые поля
        return []
    
    # Убрали дублирующиеся определения
    def get_inline_instances(self, request, obj=None):
        if obj:
            return [inline(self.model, self.admin_site) for inline in self.inlines]
        return []
    
    def response_add(self, request, obj, post_url_continue=None):
        if "_continue" in request.POST or "_addanother" in request.POST:
            return super().response_add(request, obj, post_url_continue)
        return HttpResponseRedirect(reverse('admin:main_artwork_change', args=[obj.id]))
    
    def mark_as_sold(self, request, queryset):
        updated = queryset.update(status='sold')
        self.message_user(request, f"{updated} картин помечено как проданные")
    mark_as_sold.short_description = _("Пометить как проданные")
    
    def apply_discount(self, request, queryset):
        updated_count = 0
        for artwork in queryset:
            # Проверяем, есть ли у объекта первичный ключ
            if artwork.pk and artwork.has_discount:
                artwork.price = artwork.calculate_discount_price()
                artwork.save()
                updated_count += 1
        
        if updated_count:
            self.message_user(request, f"Скидки применены к {updated_count} картинам")
        else:
            self.message_user(request, "Нет картин со скидкой для применения", level='warning')
    apply_discount.short_description = _("Применить скидку")





class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'artwork', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'shipping_method')
    search_fields = ('buyer__username', 'artwork__title')
    readonly_fields = ('created_at', 'total_price')
    fieldsets = (
        (None, {'fields': ('buyer', 'artwork')}),
        (_('Статус и стоимость'), {'fields': ('status', 'price', 'total_price')}),
        (_('Доставка'), {
            'fields': ('shipping_method', 'shipping_address', 
                       'shipping_cost', 'insurance', 'insurance_cost')
        }),
        (_('Даты'), {'fields': ('created_at',)}),
    )
    actions = ['mark_as_paid', 'mark_as_delivered']
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='paid')
        self.message_user(request, f"{updated} заказов помечено как оплаченные")
    mark_as_paid.short_description = _("Пометить как оплаченные")
    
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f"{updated} заказов помечено как доставленные")
    mark_as_delivered.short_description = _("Пометить как доставленные")

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'amount', 'method', 'status', 'created_at')
    list_filter = ('status', 'method')
    search_fields = ('order__id', 'transaction_id')
    readonly_fields = ('created_at', 'completed_at')
    fieldsets = (
        (None, {'fields': ('order', 'transaction_id')}),
        (_('Детали оплаты'), {'fields': ('amount', 'method', 'status')}),
        (_('Даты'), {'fields': ('created_at', 'completed_at')}),
    )
    actions = ['mark_as_completed']
    
    def mark_as_completed(self, request, queryset):
        for payment in queryset:
            payment.mark_as_completed()
        self.message_user(request, f"{queryset.count()} платежей помечено как завершенные")
    mark_as_completed.short_description = _("Пометить как завершенные")

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'artwork', 'rating', 'seller', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved')
    search_fields = ('artwork__title', 'seller__username')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {'fields': ('order', 'artwork', 'seller')}),
        (_('Содержание'), {'fields': ('rating', 'comment', 'is_approved')}),
        (_('Даты'), {'fields': ('created_at',)}),
    )
    actions = ['approve_reviews']
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} отзывов одобрено")
    approve_reviews.short_description = _("Одобрить выбранные отзывы")

class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'artwork', 'added_at')
    search_fields = ('user__username', 'artwork__title')
    readonly_fields = ('added_at',)

class ArtworkImageAdmin(admin.ModelAdmin):
    list_display = ('artwork', 'image_preview', 'description', 'uploaded_at')
    readonly_fields = ('uploaded_at', 'image_preview')
    search_fields = ('artwork__title',)
    
    def image_preview(self, obj):
        return format_html('<img src="{}" height="50" />', obj.image.url) if obj.image else ""
    image_preview.short_description = _('Превью')
    image_preview.allow_tags = True

class VerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'status', 'verified_at', 'is_verification_active')
    list_filter = ('status', 'document_type')
    search_fields = ('user__username', 'document_number')
    readonly_fields = ('verified_at', 'is_verification_active', 'verification_age')
    fieldsets = (
        (None, {'fields': ('user', 'document_type', 'document_number')}),
        (_('Документы'), {'fields': ('document_front', 'document_back')}),
        (_('Статус'), {'fields': ('status', 'comment', 'verified_by')}),
        (_('Верификация'), {'fields': ('verified_at', 'is_verification_active', 'verification_age')}),
    )
    actions = ['verify_users', 'reject_verifications']
    
    def verify_users(self, request, queryset):
        for verification in queryset:
            verification.status = 'verified'
            verification.verified_by = request.user
            verification.verified_at = timezone.now()
            verification.save()
        self.message_user(request, f"{queryset.count()} верификаций подтверждено")
    verify_users.short_description = _("Подтвердить верификацию")
    
    def reject_verifications(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f"{updated} верификаций отклонено")
    reject_verifications.short_description = _("Отклонить верификацию")

admin.site.register(User, CustomUserAdmin)
admin.site.register(Artist, ArtistAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Artwork, ArtworkAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ArtworkImage, ArtworkImageAdmin)
admin.site.register(Verification, VerificationAdmin)