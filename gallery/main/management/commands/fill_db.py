import os
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from main.models import (
    User, Artist, Category, Artwork, 
    Order, Payment, Review, Favorite,
    ArtworkImage, Verification
)
from decimal import Decimal

class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Начало заполнения базы данных...'))
        
        # Очистка базы данных (кроме суперпользователей)
        self.clear_db()
        
        # Создание данных
        self.create_users()
        self.create_artists()
        self.create_categories()
        self.create_artworks()
        self.create_orders()
        self.create_favorites()
        self.create_reviews()
        self.create_verifications()
        
        self.stdout.write(self.style.SUCCESS('База данных успешно заполнена!'))

    def clear_db(self):
        self.stdout.write('Очистка базы данных...')
        models = [Favorite, Review, Payment, Order, ArtworkImage, Artwork, Category, Artist, Verification]
        
        for model in models:
            model.objects.all().delete()
        
        # Удаляем только обычных пользователей
        User.objects.filter(is_superuser=False).delete()
    def create_users(self):
        self.stdout.write('Создание пользователей...')
        
        # Предопределенные пользователи
        users_data = [
            # Администраторы
            {
                'email': 'admin@galerry.ru',
                'username': 'admin',
                'first_name': 'Алексей',
                'last_name': 'Иванов',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'password': 'admin123',
                'balance': Decimal('50000.00'),  # Явное задание Decimal
                'rating': Decimal('5.00'),       # Явное задание Decimal
            },
            {
                'email': 'moderator@galerry.ru',
                'username': 'moderator',
                'first_name': 'Екатерина',
                'last_name': 'Смирнова',
                'role': 'moderator',
                'is_staff': True,
                'password': 'moderator123',
                'balance': Decimal('30000.00'),
                'rating': Decimal('4.80'),
            },
            
            # Продавцы (художники)
            {
                'email': 'anna.petrova@galerry.ru',
                'username': 'anna_artist',
                'first_name': 'Анна',
                'last_name': 'Петрова',
                'role': 'seller',
                'password': 'anna123',
                'balance': Decimal('25000.00'),
                'rating': Decimal('4.90'),
            },
            {
                'email': 'ivan.sidorov@galerry.ru',
                'username': 'ivan_artist',
                'first_name': 'Иван',
                'last_name': 'Сидоров',
                'role': 'seller',
                'password': 'ivan123',
                'balance': Decimal('18000.00'),
                'rating': Decimal('4.70'),
            },
            {
                'email': 'maria.ivanova@galerry.ru',
                'username': 'maria_artist',
                'first_name': 'Мария',
                'last_name': 'Иванова',
                'role': 'seller',
                'password': 'maria123',
                'balance': Decimal('22000.00'),
                'rating': Decimal('4.85'),
            },
            
            # Покупатели
            {
                'email': 'buyer1@example.com',
                'username': 'art_lover1',
                'first_name': 'Ольга',
                'last_name': 'Кузнецова',
                'role': 'buyer',
                'password': 'buyer123',
                'balance': Decimal('15000.00'),
                'rating': Decimal('5.00'),
            },
            {
                'email': 'buyer2@example.com',
                'username': 'art_collector',
                'first_name': 'Дмитрий',
                'last_name': 'Федоров',
                'role': 'buyer',
                'password': 'buyer123',
                'balance': Decimal('35000.00'),
                'rating': Decimal('4.95'),
            },
            {
                'email': 'buyer3@example.com',
                'username': 'gallery_visitor',
                'first_name': 'Елена',
                'last_name': 'Николаева',
                'role': 'buyer',
                'password': 'buyer123',
                'balance': Decimal('8000.00'),
                'rating': Decimal('4.60'),
            },
        ]
        
        created_count = 0
        for user_data in users_data:
            username = user_data['username']
            email = user_data['email']
            
            # Проверяем, существует ли пользователь с таким username или email
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'Пользователь {username} уже существует, пропускаем'))
                continue
                
            if User.objects.filter(email=email).exists():
                self.stdout.write(self.style.WARNING(f'Email {email} уже используется, пропускаем'))
                continue
                
            password = user_data.pop('password')
            balance = user_data.pop('balance')
            rating = user_data.pop('rating')
            
            user = User.objects.create(
                **user_data,
                balance=balance,
                rating=rating,
                is_active=True
            )
            user.set_password(password)
            user.save()
            created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Создано пользователей: {created_count}'))

    def create_artists(self):
        self.stdout.write('Создание художников...')
        
        artists_data = [
            {
                'name': 'Иван Шишкин',
                'bio': 'Выдающийся русский художник-пейзажист, живописец, рисовальщик и гравёр-аквафортист.',
                'birth_date': '1832-01-25',
                'death_date': '1898-03-20',
                'official_site': 'https://ru.wikipedia.org/wiki/Шишкин,_Иван_Иванович'
            },
            {
                'name': 'Клод Моне',
                'bio': 'Французский живописец, один из основателей импрессионизма.',
                'birth_date': '1840-11-14',
                'death_date': '1926-12-05',
                'official_site': 'https://ru.wikipedia.org/wiki/Моне,_Клод'
            },
            {
                'name': 'Василий Кандинский',
                'bio': 'Русский художник и теоретик искусства, один из основоположников абстракционизма.',
                'birth_date': '1866-12-16',
                'death_date': '1944-12-13',
                'official_site': 'https://ru.wikipedia.org/wiki/Кандинский,_Василий_Васильевич'
            },
            {
                'name': 'Фрида Кало',
                'bio': 'Мексиканская художница, наиболее известная своими автопортретами.',
                'birth_date': '1907-07-06',
                'death_date': '1954-07-13',
                'official_site': 'https://ru.wikipedia.org/wiki/Кало,_Фрида'
            },
            {
                'name': 'Пабло Пикассо',
                'bio': 'Испанский и французский художник, скульптор, график, театральный художник, керамист и дизайнер.',
                'birth_date': '1881-10-25',
                'death_date': '1973-04-08',
                'official_site': 'https://ru.wikipedia.org/wiki/Пикассо,_Пабло'
            },
            {
                'name': 'Марк Шагал',
                'bio': 'Российский, белорусский и французский художник еврейского происхождения.',
                'birth_date': '1887-07-07',
                'death_date': '1985-03-28',
                'official_site': 'https://ru.wikipedia.org/wiki/Шагал,_Марк_Захарович'
            },
        ]
        
        for artist_data in artists_data:
            Artist.objects.create(**artist_data)
        
        self.stdout.write(self.style.SUCCESS('Создано художников: {}'.format(len(artists_data))))

    def create_categories(self):
        self.stdout.write('Создание категорий...')
        
        categories_data = [
            {'name': 'Пейзаж', 'description': 'Изображения природы, сельской местности, гор, лесов, побережий.'},
            {'name': 'Портрет', 'description': 'Изображения человека или группы людей, передающие внешность и характер.'},
            {'name': 'Натюрморт', 'description': 'Изображения неодушевлённых предметов: цветов, фруктов, посуды и т.д.'},
            {'name': 'Абстракция', 'description': 'Произведения, не изображающие реальные объекты, а использующие формы и цвета для выражения идей.'},
            {'name': 'Импрессионизм', 'description': 'Направление в искусстве, характеризующееся стремлением передать мгновенные впечатления.'},
            {'name': 'Сюрреализм', 'description': 'Направление в искусстве, изображающее подсознательные образы и фантастические видения.'},
            {'name': 'Поп-арт', 'description': 'Направление в искусстве, использующее образы массовой культуры и рекламы.'},
        ]
        
        for category_data in categories_data:
            Category.objects.create(**category_data)
        
        self.stdout.write(self.style.SUCCESS('Создано категорий: {}'.format(len(categories_data))))

    def create_artworks(self):
        self.stdout.write('Создание картин...')
        
        artists = list(Artist.objects.all())
        categories = list(Category.objects.all())
        sellers = list(User.objects.filter(role='seller'))
        
        artworks_data = [
            {
                'title': 'Утро в сосновом лесу',
                'description': 'Знаменитая картина с медведями в лесу. Иван Шишкин написал пейзаж, а медведей добавил Константин Савицкий.',
                'style': 'realism',
                'medium': 'oil',
                'year_created': 1889,
                'width': Decimal('139.0'),  # Исправлено
                'height': Decimal('213.0'),  # Исправлено
                'price': Decimal('2500000.00'),  # Явное задание Decimal
                'is_framed': True,
                'is_certified': True,
            },
            {
                'title': 'Водяные лилии',
                'description': 'Серия картин Клода Моне, изображающих его цветочный сад в Живерни.',
                'style': 'impressionism',
                'medium': 'oil',
                'year_created': 1915,
                'width': Decimal('200.0'),
                'height': Decimal('180.0'),
                'price': Decimal('3500000.00'),
                'is_framed': True,
            },
            {
                'title': 'Композиция VIII',
                'description': 'Абстрактная работа Кандинского, демонстрирующая его теорию о духовном в искусстве.',
                'style': 'abstract',
                'medium': 'oil',
                'year_created': 1923,
                'width': Decimal('140.0'),
                'height': Decimal('201.0'),
                'price': Decimal('4200000.00'),
                'is_certified': True,
            },
            {
                'title': 'Две Фриды',
                'description': 'Одна из самых известных картин Фриды Кало, изображающая две ипостаси художницы.',
                'style': 'surrealism',
                'medium': 'oil',
                'year_created': 1939,
                'width': Decimal('173.0'),
                'height': Decimal('173.0'),
                'price': Decimal('5000000.00'),
                'is_framed': True,
                'is_certified': True,
            },
            {
                'title': 'Герника',
                'description': 'Мощная антивоенная картина Пикассо, созданная в ответ на бомбардировку Герники.',
                'style': 'cubism',
                'medium': 'oil',
                'year_created': 1937,
                'width': Decimal('349.0'),
                'height': Decimal('776.0'),
                'price': Decimal('10000000.00'),
                'is_certified': True,
            },
            {
                'title': 'Над городом',
                'description': 'Одна из самых известных работ Марка Шагала, изображающая его и жену Беллу, летящих над Витебском.',
                'style': 'expressionism',
                'medium': 'oil',
                'year_created': 1918,
                'width': Decimal('141.0'),
                'height': Decimal('197.0'),
                'price': Decimal('3800000.00'),
                'is_framed': True,
            },
            {
                'title': 'Золотая осень',
                'description': 'Живописный осенний пейзаж с золотыми березами и тихой рекой.',
                'style': 'realism',
                'medium': 'oil',
                'year_created': 2020,
                'width': Decimal('80.0'),
                'height': Decimal('60.0'),
                'price': Decimal('120000.00'),
            },
            {
                'title': 'Морской закат',
                'description': 'Импрессионистическое изображение заката над морем с яркими цветами и размытыми формами.',
                'style': 'impressionism',
                'medium': 'acrylic',
                'year_created': 2021,
                'width': Decimal('100.0'),
                'height': Decimal('70.0'),
                'price': Decimal('85000.00'),
                'is_framed': True,
            },
            {
                'title': 'Городские огни',
                'description': 'Ночной городской пейзаж с неоновыми огнями и отражениями в мокром асфальте.',
                'style': 'realism',
                'medium': 'oil',
                'year_created': 2022,
                'width': Decimal('90.0'),
                'height': Decimal('60.0'),
                'price': Decimal('150000.00'),
                'is_certified': True,
            },
            {
                'title': 'Весеннее пробуждение',
                'description': 'Абстрактная интерпретация весны с пастельными тонами и плавными линиями.',
                'style': 'abstract',
                'medium': 'acrylic',
                'year_created': 2023,
                'width': Decimal('120.0'),
                'height': Decimal('90.0'),
                'price': Decimal('95000.00'),
            },
        ]
        
        # ... остальной код без изменений
        
        statuses = ['active', 'active', 'active', 'sold', 'reserved', 'active', 'active', 'active', 'active', 'active']
        created_ats = [
            datetime.now() - timedelta(days=10),
            datetime.now() - timedelta(days=30),
            datetime.now() - timedelta(days=100),
            datetime.now() - timedelta(days=200),
            datetime.now() - timedelta(days=365),
            datetime.now() - timedelta(days=15),
            datetime.now() - timedelta(days=40),
            datetime.now() - timedelta(days=120),
            datetime.now() - timedelta(days=180),
            datetime.now() - timedelta(days=20),
        ]
        
        for i, artwork_data in enumerate(artworks_data):
            # Для первых 6 работ используем известных художников, остальные - современные
            artist = artists[i % len(artists)] if i < 6 else None
            
            # Продавец (художник)
            seller = sellers[i % len(sellers)]
            
            # Категория
            if 'пейзаж' in artwork_data['title'].lower():
                category = Category.objects.get(name='Пейзаж')
            elif 'фрида' in artwork_data['title'].lower():
                category = Category.objects.get(name='Портрет')
            else:
                category = random.choice(categories)
            
            artwork = Artwork.objects.create(
                seller=seller,
                artist=artist,
                category=category,
                status=statuses[i],
                created_at=created_ats[i],
                **artwork_data
            )
            
            # Создание дополнительных изображений для некоторых картин
            if i % 2 == 0:  # Каждая вторая картина
                ArtworkImage.objects.create(
                    artwork=artwork,
                    description='Детали картины'
                )
                if i % 3 == 0:  # Каждая третья
                    ArtworkImage.objects.create(
                        artwork=artwork,
                        description='Рамка и подпись художника'
                    )
        
        self.stdout.write(self.style.SUCCESS('Создано картин: {}'.format(len(artworks_data))))

    def create_orders(self):
        self.stdout.write('Создание заказов...')
        
        # Получаем ВСЕ картины, а не только sold/reserved
        all_artworks = Artwork.objects.all()
        buyers = list(User.objects.filter(role='buyer'))
        
        # Используем только существующие индексы
        orders_data = []
        
        if all_artworks.count() > 3:
            orders_data.append({
                'artwork': all_artworks[3],  # "Две Фриды"
                'buyer': buyers[0],
                'status': 'completed',
                'shipping_address': 'Москва, ул. Тверская, д. 10, кв. 25',
                'shipping_method': 'courier',
                'shipping_cost': Decimal('1500.00'),  # Исправлено на Decimal
                'insurance': True,
                'insurance_cost': Decimal('5000.00'),  # Исправлено на Decimal
            })
        
        if all_artworks.count() > 4:
            orders_data.append({
                'artwork': all_artworks[4],  # "Герника"
                'buyer': buyers[1],
                'status': 'paid',
                'shipping_address': 'Санкт-Петербург, Невский пр-т, д. 45',
                'shipping_method': 'express',
                'shipping_cost': Decimal('3500.00'),  # Исправлено на Decimal
                'insurance': True,
                'insurance_cost': Decimal('10000.00'),  # Исправлено на Decimal
            })
        
        if all_artworks.count() > 5:
            orders_data.append({
                'artwork': all_artworks[5],  # "Над городом"
                'buyer': buyers[2],
                'status': 'reserved',
                'shipping_address': 'Екатеринбург, ул. Ленина, д. 32',
                'shipping_method': 'post',
                'shipping_cost': Decimal('800.00'),  # Исправлено на Decimal
            })
        
        for order_data in orders_data:
            artwork = order_data.pop('artwork')
            order = Order.objects.create(
                artwork=artwork,
                price=artwork.price,
                created_at=datetime.now() - timedelta(days=random.randint(1, 30)),
                **order_data
            )
            
            # Создание платежа для завершенных заказов
            if order.status in ['paid', 'completed']:
                Payment.objects.create(
                    order=order,
                    amount=order.total_price,
                    method='card' if order.status == 'completed' else 'bank',
                    transaction_id='TX' + str(random.randint(1000000, 9999999)),
                    status='completed',
                    completed_at=order.created_at + timedelta(days=1)
                )
        
        self.stdout.write(self.style.SUCCESS('Создано заказов: {}'.format(len(orders_data))))
    def create_favorites(self):
        self.stdout.write('Создание избранного...')
        
        users = User.objects.all()
        artworks = Artwork.objects.filter(status='active')
        
        # Каждый пользователь добавляет 1-3 картины в избранное
        favorites = [
            (users[0], artworks[0]),  # Ольга -> Утро в сосновом лесу
            (users[0], artworks[6]),  # Ольга -> Золотая осень
            (users[1], artworks[1]),  # Дмитрий -> Водяные лилии
            (users[1], artworks[4]),  # Дмитрий -> Герника
            (users[2], artworks[2]),  # Елена -> Композиция VIII
            (users[2], artworks[9]),  # Елена -> Весеннее пробуждение
            (users[3], artworks[3]),  # Анна -> Две Фриды (своя работа)
            (users[4], artworks[7]),  # Иван -> Морской закат
            (users[5], artworks[8]),  # Мария -> Городские огни
        ]
        
        for user, artwork in favorites:
            Favorite.objects.create(user=user, artwork=artwork)
        
        self.stdout.write(self.style.SUCCESS('Создано избранных элементов: {}'.format(len(favorites))))

    def create_reviews(self):
        self.stdout.write('Создание отзывов...')
        
        completed_orders = Order.objects.filter(status='completed')
        
        reviews_data = []
        
        if completed_orders.exists():
            reviews_data.append({
                'order': completed_orders[0],
                'rating': 5,
                'comment': 'Прекрасная картина, отличное качество исполнения! Доставка была быстрой и аккуратной.',
            })
            reviews_data.append({
                'order': completed_orders[0],
                'rating': 4,
                'comment': 'Картина понравилась, но рама пришла с небольшим повреждением. Продавец оперативно решил проблему.',
            })
        
        for review_data in reviews_data:
            order = review_data.pop('order')
            Review.objects.create(
                order=order,
                seller=order.artwork.seller,
                artwork=order.artwork,
                is_approved=True,
                **review_data
            )
        
        self.stdout.write(self.style.SUCCESS('Создано отзывов: {}'.format(len(reviews_data))))

    def create_verifications(self):
        self.stdout.write('Создание верификаций...')
        
        sellers = User.objects.filter(role='seller')
        
        verifications_data = [
            {
                'user': sellers[0],  # Анна
                'document_type': 'passport',
                'document_number': '4510123456',
                'status': 'verified',
            },
            {
                'user': sellers[1],  # Иван
                'document_type': 'driver_license',
                'document_number': '99AA123456',
                'status': 'pending',
            },
            {
                'user': sellers[2],  # Мария
                'document_type': 'id_card',
                'document_number': '123-456-789',
                'status': 'verified',
            },
        ]
        
        for verification_data in verifications_data:
            Verification.objects.create(**verification_data)
        
        self.stdout.write(self.style.SUCCESS('Создано верификаций: {}'.format(len(verifications_data))))