# main/serializers.py
from rest_framework import serializers
from .models import Artwork, Artist, Category, Review, Order
from django.urls import reverse

class ArtistSerializer(serializers.ModelSerializer):
    artworks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Artist
        fields = ['id', 'name', 'bio', 'photo', 'artworks_count']
    
    def get_artworks_count(self, obj):
        return obj.artworks.count()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'icon']

class ArtworkSerializer(serializers.ModelSerializer):
    artist = ArtistSerializer()
    category = CategorySerializer()
    seller = serializers.StringRelatedField()
    discount_info = serializers.SerializerMethodField()
    dimensions = serializers.SerializerMethodField()
    absolute_url = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()
    
    class Meta:
        model = Artwork
        fields = [
            'id', 'title', 'artist', 'category', 'seller', 
            'price', 'image', 'status', 'created_at',
            'discount_info', 'dimensions', 'absolute_url',
            'is_favorite', 'style', 'medium', 'year_created'
        ]
    
    def get_discount_info(self, obj):
        return {
            'has_discount': obj.has_discount,
            'discounted_price': str(obj.discounted_price),
            'discount_percentage': str(obj.discount_percentage * 100)
        }
    
    def get_dimensions(self, obj):
        return obj.dimensions()
    
    def get_absolute_url(self, obj):
        return reverse('main:artwork_detail', kwargs={'pk': obj.pk})
    
    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.in_favorites.filter(user=request.user).exists()
        return False

class ReviewSerializer(serializers.ModelSerializer):
    buyer = serializers.StringRelatedField()
    artwork_title = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'created_at', 'buyer', 'artwork_title']
    
    def get_artwork_title(self, obj):
        return obj.artwork.title

class OrderSerializer(serializers.ModelSerializer):
    artwork = ArtworkSerializer()
    buyer = serializers.StringRelatedField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'artwork', 'buyer', 'price', 'status', 
            'status_display', 'created_at', 'total_price'
        ]
    
    def get_status_display(self, obj):
        return obj.get_status_display()