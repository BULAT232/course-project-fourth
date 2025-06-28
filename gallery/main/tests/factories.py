# main/tests/factories.py
import factory
from factory.django import DjangoModelFactory
from main.models import Artwork, User, Artist, Category
from django.utils import timezone

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        
    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.Sequence(lambda n: f'user_{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password123')

class ArtistFactory(DjangoModelFactory):
    class Meta:
        model = Artist
        
    name = factory.Faker('name')
    bio = factory.Faker('text')

class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category
        
    name = factory.Faker('word')
    description = factory.Faker('sentence')

class ArtworkFactory(DjangoModelFactory):
    class Meta:
        model = Artwork
        
    title = factory.Faker('sentence', nb_words=3)
    seller = factory.SubFactory(UserFactory)
    artist = factory.SubFactory(ArtistFactory)
    category = factory.SubFactory(CategoryFactory)
    year_created = factory.Faker('year')
    width = factory.Faker('pyfloat', positive=True, min_value=10, max_value=200)
    height = factory.Faker('pyfloat', positive=True, min_value=10, max_value=200)
    price = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    description = factory.Faker('text')
    status = 'active'
    created_at = factory.LazyFunction(timezone.now)