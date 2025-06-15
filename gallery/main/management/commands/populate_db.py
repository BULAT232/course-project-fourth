# main/management/commands/populate_db.py
import random
import uuid
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from main.models import (
    Game, Platform, GamePlatform, Account, AccountPlatform,
    Order, Payment, Review, Message, Verification, Favorite
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate the database with sample data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting DB population...'))
        games = self.create_games()
        platforms = self.create_platforms()
        self.create_game_platforms(games, platforms)
        users = self.create_users()
        accounts = self.create_accounts(users, games)
        self.create_account_platforms(accounts, platforms)
        orders = self.create_orders(users, accounts)
        self.create_payments(orders)
        self.create_reviews(orders)
        self.create_messages(orders)
        self.create_verifications(users)
        self.create_favorites(users, games)
        self.stdout.write(self.style.SUCCESS('Database populated successfully.'))

    def generate_username(self):
        return f'user_{random.randint(1000, 9999)}'

    def generate_text(self):
        words = ["Lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit"]
        return ' '.join(random.choices(words, k=random.randint(5, 15))) + '.'

    def generate_catch_phrase(self):
        prefixes = ["Awesome", "Epic", "Pro", "Golden", "Legendary", "Mythic"]
        suffixes = ["Account", "Gaming", "Edition", "Collection", "Bundle"]
        return f"{random.choice(prefixes)} {random.choice(suffixes)}"

    def generate_date(self, past_days=365):
        return timezone.now() - timedelta(days=random.randint(1, past_days))

    def create_games(self):
        data = [
            {'name': 'Counter-Strike 2', 'official_site': 'https://www.counter-strike.net'},
            {'name': 'Dota 2', 'official_site': 'https://www.dota2.com'},
            {'name': 'Apex Legends', 'official_site': 'https://www.ea.com/games/apex-legends'},
            {'name': 'World of Warcraft', 'official_site': 'https://worldofwarcraft.blizzard.com'},
            {'name': 'Fortnite', 'official_site': 'https://www.fortnite.com'},
        ]
        return [Game.objects.create(**item) for item in data]

    def create_platforms(self):
        names = ['PC', 'PlayStation', 'Xbox', 'Mobile']
        return [Platform.objects.create(name=name) for name in names]

    def create_game_platforms(self, games, platforms):
        for game in games:
            for platform in random.sample(platforms, k=random.randint(1, 3)):
                GamePlatform.objects.create(game=game, platform=platform)

    def create_users(self):
        users = []
        roles = ['buyer', 'seller', 'moderator', 'admin']
        admin = User.objects.create_superuser(
            email='admin@example.com', username='admin', password='adminpass', role='admin'
        )
        users.append(admin)
        for i in range(1, 11):
            user = User.objects.create_user(
                email=f'user{i}@example.com',
                username=self.generate_username(),
                password='testpass123',
                role=random.choice(roles),
                balance=random.uniform(0, 500)
            )
            users.append(user)
        return users

    def create_accounts(self, users, games):
        accounts = []
        statuses = ['active', 'sold', 'reserved', 'banned']
        sellers = [u for u in users if u.role == 'seller'] or users[:2]
        for seller in sellers:
            for _ in range(random.randint(3, 6)):
                game = random.choice(games)
                account = Account.objects.create(
                    seller=seller,
                    game=game,
                    title=self.generate_catch_phrase(),
                    description=self.generate_text(),
                    attributes={'level': random.randint(1, 100), 'rank': self.generate_text(), 'characters': [f'Char_{i}' for i in range(1, 4)]},
                    price=random.uniform(5, 500),
                    status=random.choice(statuses),
                    vac_status=random.choice([True, False]),
                    created_at=self.generate_date()
                )
                accounts.append(account)
        return accounts

    def create_account_platforms(self, accounts, platforms):
        for account in accounts:
            gps = GamePlatform.objects.filter(game=account.game)
            for gp in random.sample(list(gps), k=min(len(gps), 2)):
                AccountPlatform.objects.create(account=account, platform=gp.platform, game=account.game)

    def create_orders(self, users, accounts):
        orders = []
        statuses = ['created', 'paid', 'delivered', 'completed', 'disputed', 'cancelled']
        buyers = [u for u in users if u.role == 'buyer'] or users[2:5]
        for _ in range(15):
            acct = random.choice(accounts)
            if acct.status != 'active':
                acct.status = 'active'
                acct.save()
            order = Order.objects.create(
                buyer=random.choice(buyers),
                account=acct,
                price=acct.price,
                status=random.choice(statuses),
                warranty_days=random.randint(7, 30),
                created_at=self.generate_date(90)
            )
            orders.append(order)
        return orders

    def create_payments(self, orders):
        methods = ['paypal', 'card', 'crypto', 'qiwi']
        for order in orders:
            if order.status in ['paid', 'delivered', 'completed']:
                Payment.objects.create(order=order, amount=order.price, method=random.choice(methods), transaction_id=str(uuid.uuid4()), status='completed')

    def create_reviews(self, orders):
        for order in orders:
            if order.status == 'completed':
                Review.objects.create(order=order, seller=order.account.seller, rating=random.randint(1, 5), comment=self.generate_text())

    def create_messages(self, orders):
        for order in orders:
            parties = [order.buyer, order.account.seller]
            for _ in range(random.randint(1, 3)):
                frm = random.choice(parties)
                to = parties[1] if frm == parties[0] else parties[0]
                Message.objects.create(order=order, from_user=frm, to_user=to, content=self.generate_text())

    def create_verifications(self, users):
        for user in random.sample(users, 5):
            Verification.objects.create(user=user, document_type=random.choice(['passport', 'driver_license', 'id_card']), document_number=str(random.randint(1000, 9999)), status=random.choice(['pending', 'verified', 'rejected']), verified_at=self.generate_date(180) if random.choice([True, False]) else None)

    def create_favorites(self, users, games):
        for user in users:
            for game in random.sample(games, k=random.randint(1, 3)):
                Favorite.objects.create(user=user, game=game)

# Не забудьте создать __init__.py в main/management и main/management/commands
