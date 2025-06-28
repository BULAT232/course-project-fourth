from .models import User

def create_user(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}

    # Данные от Яндекса
    email = details.get('email')
    first_name = details.get('first_name', '')
    last_name = details.get('last_name', '')
    social_id = kwargs.get('response', {}).get('id')

    # Генерация username (если email не предоставлен)
    if not email:
        email = f"{social_id}@yandex-social.ru"
    
    # Создание уникального username
    base_username = email.split('@')[0]
    username = base_username
    counter = 1
    
    while User.objects.filter(username=username).exists():
        username = f"{base_username}_{counter}"
        counter += 1

    # Создаем пользователя
    user = User.objects.create(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name,
        social_id=social_id,
        is_active=True,
        role='buyer'  # Роль по умолчанию
    )
    
    return {
        'is_new': True,
        'user': user
    }


from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

def register_via_social(backend, details, response, *args, **kwargs):
    # Проверяем, что это процесс регистрации
    if not kwargs.get('is_new'):
        return None
    
    user = kwargs.get('user')
    if not user:
        return None
    
    # Дополняем данные пользователя
    user.first_name = details.get('first_name', '')
    user.last_name = details.get('last_name', '')
    
    # Устанавливаем роль по умолчанию
    user.role = 'buyer'
    
    try:
        user.save()
        return {'user': user}
    except IntegrityError as e:
        # Обработка ошибок сохранения
        return None

# В settings.py добавьте этот пайплайн
