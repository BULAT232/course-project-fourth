# main/tests/test_tasks.py
from django.test import TestCase, override_settings
from django.utils import timezone
from main.models import Artwork, User, Artist, Category
from main.tasks import deactivate_old_artworks
from datetime import timedelta
import time

@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True
)
class DeactivateArtworksTest(TestCase):
    def setUp(self):
        # Создаем пользователя
        self.user = User.objects.create_user(
            username='test_artist',
            email='artist@example.com',
            password='testpass123'
        )
        
        # Создаем художника
        self.artist = Artist.objects.create(
            name="Test Artist",
            bio="Test bio"
        )
        
        # Создаем категорию
        self.category = Category.objects.create(
            name="Test Category",
            description="Test description"
        )
        
        # Создаем картины с текущим временем
        self.old_artwork = Artwork.objects.create(
            title="Old Painting",
            seller=self.user,
            artist=self.artist,
            category=self.category,
            status='active',
            year_created=2000,
            width=100.0,
            height=80.0,
            price=10000.00,
            description="Old painting description",
        )
        
        self.new_artwork = Artwork.objects.create(
            title="New Painting",
            seller=self.user,
            artist=self.artist,
            category=self.category,
            status='active',
            year_created=2023,
            width=120.0,
            height=90.0,
            price=15000.00,
            description="New painting description",
        )
        
        # Ждем немного, чтобы время изменилось
        time.sleep(0.1)
        
        # Обновляем даты создания напрямую через UPDATE
        old_date = timezone.now() - timedelta(days=31)
        Artwork.objects.filter(id=self.old_artwork.id).update(created_at=old_date)
        
        new_date = timezone.now() - timedelta(days=29)
        Artwork.objects.filter(id=self.new_artwork.id).update(created_at=new_date)
        
        # Перезагружаем объекты из базы
        self.old_artwork.refresh_from_db()
        self.new_artwork.refresh_from_db()

    def test_deactivate_old_artworks(self):
        # Проверяем начальное состояние
        self.assertEqual(Artwork.objects.filter(status='active').count(), 2)
        
        # Проверяем даты создания
        now = timezone.now()
        self.assertTrue(self.old_artwork.created_at < now - timedelta(days=30))
        self.assertTrue(self.new_artwork.created_at > now - timedelta(days=30))
        
        # Выполняем задачу
        result = deactivate_old_artworks.delay()
        
        # Проверяем результат выполнения задачи
        self.assertEqual(result.get(), "Деактивировано 1 картин")
        
        # Проверяем результаты
        self.old_artwork.refresh_from_db()
        self.new_artwork.refresh_from_db()
        
        self.assertEqual(self.old_artwork.status, 'archived')
        self.assertEqual(self.new_artwork.status, 'active')
        self.assertEqual(Artwork.objects.filter(status='active').count(), 1)

