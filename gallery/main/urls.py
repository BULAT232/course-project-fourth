
from django.urls import path
from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArtworkViewSet, ArtistViewSet, CategoryViewSet, CustomAuthToken, ReviewViewSet, OrderViewSet, trigger_test_error
app_name = 'main'

router = DefaultRouter()
router.register(r'artworks', ArtworkViewSet)
router.register(r'artists', ArtistViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'orders', OrderViewSet)



urlpatterns = [
    path('', views.home, name='home'),
    path('test-error/', trigger_test_error, name='test-error'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('cart/add/<int:artwork_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/remove/<int:order_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('artwork/<int:pk>/', views.artwork_detail, name='artwork_detail'),
    path('cart/checkout/', views.checkout_view, name='checkout'),
    path('admin/users/', views.admin_user_management, name='admin_user_management'),
    path('admin/users/<int:user_id>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('admin/artworks/create/', views.admin_artwork_create, name='admin_artwork_create'),
    path('admin/artworks/<int:artwork_id>/edit/', views.admin_artwork_edit, name='admin_artwork_edit'),
    path('admin/artworks/<int:artwork_id>/delete/', views.admin_artwork_delete, name='admin_artwork_delete'),
    path('admin/artworks/search/', views.admin_artwork_search, name='admin_artwork_search'),
    path('checkout/', views.checkout_view, name='checkout_view'),
    path('api/get-token/', CustomAuthToken.as_view(), name='get_token'),
    path('api/', include(router.urls)),

 
]
    

