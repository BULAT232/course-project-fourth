from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import User

@receiver(post_migrate)
def create_admin(sender, **kwargs):
    if not User.objects.filter(email='admin@example.com').exists():
        User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='securepassword123',
            role='admin',
            is_admin=True
        )