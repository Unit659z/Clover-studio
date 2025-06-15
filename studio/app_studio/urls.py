from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'app_studio'

# --- DRF Router ---
router = DefaultRouter()

router.register(r'services', views.ServiceViewSet, basename='service-api')
router.register(r'executors', views.ExecutorViewSet, basename='executor-api')
router.register(r'orders', views.OrderViewSet, basename='order-api')
router.register(r'news', views.NewsViewSet, basename='news-api')
router.register(r'portfolios', views.PortfolioViewSet, basename='portfolio-api')
router.register(r'reviews', views.ReviewViewSet, basename='review-api')
router.register(r'order-statuses', views.OrderStatusViewSet, basename='orderstatus-api')
router.register(r'messages', views.MessageViewSet, basename='message-api')


urlpatterns = [
    path('api/', include(router.urls)), # Все API URL теперь /studio/api/...
    
    path('api/auth/login/', views.LoginView.as_view(), name='api-login'),
    path('api/auth/logout/', views.LogoutView.as_view(), name='api-logout'),
    path('api/auth/status/', views.SessionStatusView.as_view(), name='api-session-status'),
    path('api/auth/csrf/', views.GetCSRFTokenView.as_view(), name='api-get-csrf'),
    path('api/auth/register/', views.RegisterView.as_view(), name='api-register'),
    path('api/auth/password/change/', views.PasswordChangeView.as_view(), name='api-password-change'),
    path('api/profile/', views.UserProfileView.as_view(), name='user-profile-api'),
    path('api/cart/', views.CartViewSet.as_view({'get': 'list',}), name='cart-api-detail'), 
    path('api/cart/items/', views.CartViewSet.as_view({'post': 'add_item', }), name='cart-api-add-item'),
    path('api/cart/items/<int:item_pk>/', views.CartViewSet.as_view({'patch': 'update_item_quantity','delete': 'remove_item',}), name='cart-api-item-detail'),
    path('api/cart/clear/', views.CartViewSet.as_view({'delete': 'clear_cart',}), name='cart-api-clear'),

    path('services/<int:pk>/details/', views.service_detail, name='service_detail'),
    path('executors/<int:pk>/details/', views.executor_detail_placeholder, name='executor_detail'),
    path('users/<int:pk>/', views.user_detail_placeholder, name='user_detail'), 
    path('news/<int:pk>/details/', views.news_detail_placeholder, name='news_detail'),
    path('cart/', views.cart_detail_placeholder, name='cart_detail'), 
    path('portfolios/<int:pk>/details/', views.portfolio_detail_placeholder, name='portfolio_detail'),
    path('old/orders/<int:pk>/', views.order_detail, name='old_order_detail'),

    path('sentry-test-error/', views.trigger_sentry_error, name='sentry-test-error'),
]
