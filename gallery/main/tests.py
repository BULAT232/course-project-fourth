from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Category, Artwork, Artist, Order
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class HomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Test Category")
        self.artist = Artist.objects.create(name="Test Artist")
        
        self.seller = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='testpass',
            role='seller'
        )
        
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'simple image content',
            content_type='image/jpeg'
        )
        
        self.artwork = Artwork.objects.create(
            title="Test Artwork",
            price=10000,
            status='active',
            artist=self.artist,
            category=self.category,
            seller=self.seller,
            year_created=2020,
            width=50,
            height=60,
            image=image
        )

    def test_home_view(self):
        response = self.client.get(reverse('main:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Category")
        self.assertContains(response, "Test Artwork")


class RegisterViewTest(TestCase):
    def test_register_view_get(self):
        response = self.client.get(reverse('main:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Регистрация")

    def test_register_view_post_success(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
            'role': 'buyer'
        }
        response = self.client.post(reverse('main:register'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='testuser').exists())


class LoginLogoutViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com',
            is_active=True
        )

    def test_login_view_get(self):
        response = self.client.get(reverse('main:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Вход")

    def test_logout_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('main:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('main:home'))


class ProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com',
            is_active=True
        )
        self.client.force_login(self.user)

    def test_profile_view_get(self):
        response = self.client.get(reverse('main:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Профиль")


class CartViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com',
            is_active=True
        )
        self.client.force_login(self.user)
        
        self.category = Category.objects.create(name="Test Category")
        self.artist = Artist.objects.create(name="Test Artist")
        
        self.seller = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='testpass',
            role='seller'
        )
        
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'simple image content',
            content_type='image/jpeg'
        )
        
        self.artwork = Artwork.objects.create(
            title="Test Artwork",
            price=20000,
            status='active',
            artist=self.artist,
            category=self.category,
            seller=self.seller,
            year_created=2020,
            width=50,
            height=60,
            image=image
        )

    def test_add_to_cart(self):
        url = reverse('main:add_to_cart', args=[self.artwork.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Order.objects.filter(artwork=self.artwork).exists())

    def test_cart_view(self):
        Order.objects.create(
            buyer=self.user,
            artwork=self.artwork,
            price=self.artwork.price,
            status='created'
        )
        response = self.client.get(reverse('main:cart_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Artwork")

    def test_remove_from_cart(self):
        order = Order.objects.create(
            buyer=self.user,
            artwork=self.artwork,
            price=self.artwork.price,
            status='created'
        )
        url = reverse('main:remove_from_cart', args=[order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Order.objects.filter(id=order.id).exists())


class CheckoutViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com',
            is_active=True
        )
        self.client.force_login(self.user)
        
        self.category = Category.objects.create(name="Test Category")
        self.artist = Artist.objects.create(name="Test Artist")
        
        self.seller = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='testpass',
            role='seller'
        )
        
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'simple image content',
            content_type='image/jpeg'
        )
        
        self.artwork = Artwork.objects.create(
            title="Test Artwork",
            price=20000,
            status='active',
            artist=self.artist,
            category=self.category,
            seller=self.seller,
            year_created=2020,
            width=50,
            height=60,
            image=image
        )
        Order.objects.create(
            buyer=self.user,
            artwork=self.artwork,
            price=self.artwork.price,
            status='created'
        )

    def test_checkout_view(self):
        response = self.client.get(reverse('main:checkout_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Оформление заказа")