import django_filters
from .models import Artwork

class ArtworkAdminFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains', label='Название')
    artist__name = django_filters.CharFilter(lookup_expr='icontains', label='Художник')
    seller__username = django_filters.CharFilter(lookup_expr='icontains', label='Продавец')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte', label='Мин. цена')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte', label='Макс. цена')
    status = django_filters.ChoiceFilter(choices=Artwork.STATUS_CHOICES, label='Статус')
    
    class Meta:
        model = Artwork
        fields = ['title', 'artist__name', 'seller__username', 'status']