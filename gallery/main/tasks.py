# main/tasks.py
from celery import shared_task
from .models import Artwork, Verification, Order
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def deactivate_old_artworks():
    """Деактивирует картины старше 30 дней"""
    threshold = timezone.now() - timedelta(days=30)
    old_artworks = Artwork.objects.filter(
        created_at__lte=threshold, 
        status='active'
    )
    count = old_artworks.update(status='archived')
    return f"Деактивировано {count} картин"

@shared_task
def check_unverified_sellers():
    """Проверяет неподтвержденных продавцов"""
    unverified = Verification.objects.filter(
        status='pending',
        created_at__lte=timezone.now() - timedelta(days=3)
    )
    
    for seller in unverified:
        subject = 'Требуется верификация продавца'
        message = f'Продавец {seller.user.username} ожидает верификации более 3 дней'
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=False,
        )
    
    return f"Отправлено {unverified.count()} уведомлений"

@shared_task
def cleanup_expired_carts():
    """Очищает корзины старше 7 дней"""
    expired = timezone.now() - timedelta(days=7)
    expired_orders = Order.objects.filter(
        status='created',
        created_at__lte=expired
    )
    count = expired_orders.delete()[0]
    return f"Удалено {count} просроченных корзин"