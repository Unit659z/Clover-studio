from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Avg, Sum, F, Q
from django.contrib import messages

from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import login as django_login 
from rest_framework import views, permissions, status, generics
from rest_framework.response import Response
from rest_framework import viewsets, permissions, status, mixins, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend

from .permissions import IsOwnerOrReadOnly, IsCartOwner, IsMessageParticipantOrReadOnly, IsAdminOrExecutorOrReadOnly, IsPortfolioOwnerOrAdminOrReadOnly, IsAdminOrReadOnly

from .models import (
    Service, Order, CustomUser, Executor, OrderStatus, News, Cart, CostCalculator,
    Portfolio, Review, Message, CartItem, ExecutorService
)
from .serializers import (
    ServiceSerializer, ExecutorSerializer, OrderReadSerializer, OrderWriteSerializer,
    NewsSerializer, PortfolioSerializer, ReviewSerializer, OrderStatusSerializer,
    UserSerializer, CartSerializer, CartItemSerializer, MessageSerializer,
    ExecutorServiceSerializer, RegisterSerializer, PasswordChangeSerializer 
)

class PasswordChangeView(generics.GenericAPIView):
    """ API View для смены пароля аутентифицированным пользователем. """
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        # Передаем request в контекст для доступа к user в validate_old_password
        serializer.is_valid(raise_exception=True)

        user = request.user
        # Устанавливаем новый пароль (сериализатор уже проверил совпадение и валидность)
        user.set_password(serializer.validated_data['new_password1'])
        user.save()

        #Обновляем хэш сессии, чтобы пользователь не разлогинился 
        update_session_auth_hash(request, user)

        return Response({"detail": "Пароль успешно изменен."}, status=status.HTTP_200_OK)

class RegisterView(generics.CreateAPIView):
    """
    API View для регистрации новых пользователей.
    АВТОМАТИЧЕСКИ АУТЕНТИФИЦИРУЕТ пользователя после успешной регистрации.
    """
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Указываем путь к стандартному ModelBackend, его достаточно для сессии
        backend_path = 'django.contrib.auth.backends.ModelBackend'

        # Проверяем, что бэкенд действительно есть в настройках (на всякий случай)
        from django.conf import settings
        if backend_path in settings.AUTHENTICATION_BACKENDS:
            user.backend = backend_path 
            django_login(request, user)
            print(f"User {user.username} automatically logged in after registration.")
        else:
            # Если бэкенд не найден, логируем ошибку, но не ломаем запрос
            print(f"ERROR: Specified backend '{backend_path}' not found in AUTHENTICATION_BACKENDS. User not logged in.")
            # Регистрация все равно прошла успешно, но без авто-логина


        user_data_serializer = UserSerializer(user, context=self.get_serializer_context())
        headers = self.get_success_headers(user_data_serializer.data)
        return Response(user_data_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
class LoginView(views.APIView):
    """
    API View для входа пользователя по имени пользователя ИЛИ email и паролю.
    Устанавливает sessionid cookie.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        # Получаем один идентификатор (может быть username или email)
        identifier = request.data.get('identifier') # Ожидаем ключ 'identifier' от фронта
        password = request.data.get('password')

        if not identifier or not password:
            return Response(
                {'detail': 'Необходимо указать имя пользователя/email и пароль.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Передаем идентификатор как username в authenticate.
        user = authenticate(request, username=identifier, password=password)

        if user is not None:
            # Проверяем, активен ли пользователь (на всякий случай)
            if not user.is_active:
                 return Response(
                     {'detail': 'Аккаунт пользователя неактивен.'},
                     status=status.HTTP_401_UNAUTHORIZED
                 )

            django_login(request, user)
            serializer = UserSerializer(user, context={'request': request})
            return Response(serializer.data)
        else:
            # Пользователь не найден ИЛИ пароль неверный ИЛИ пользователь неактивен 
            return Response(
                {'detail': 'Неверные учетные данные или аккаунт неактивен.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

class LogoutView(views.APIView):
    """ API View для выхода пользователя. Удаляет сессию. """
    permission_classes = [permissions.IsAuthenticated] # Только залогиненные могут выйти

    def post(self, request, *args, **kwargs):
        # Используем стандартный logout Django
        django_logout(request)
        return Response(
            {'detail': 'Выход выполнен успешно.'},
            status=status.HTTP_200_OK
        )

class SessionStatusView(views.APIView):
    """
    Проверяет, аутентифицирован ли пользователь по сессии.
    Возвращает данные пользователя или 401/403.
    Также полезно для получения CSRF cookie при первом GET запросе.
    """
    permission_classes = [permissions.IsAuthenticated] # Требуем аутентификацию

    @method_decorator(ensure_csrf_cookie) # Гарантированно ставим CSRF куки при GET
    def get(self, request, *args, **kwargs):
        # пользователь аутентифицирован
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

# Оставляем UserProfileView для получения/обновления профиля
class UserProfileView(generics.RetrieveUpdateAPIView):
    """API для получения и обновления профиля текущего пользователя."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ---  CSRF токен ---
class GetCSRFTokenView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request, *args, **kwargs):
        # Просто возвращаем CSRF токен, чтобы клиент мог его использовать
        return Response({'detail': 'CSRF cookie set.', 'csrfToken': get_token(request)})

# --- Стандартная Пагинация ---
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10 # Количество элементов на странице по умолчанию
    page_size_query_param = 'page_size' # Параметр для указания кол-ва элементов ?page_size=20
    max_page_size = 100 # Максимальное кол-во элементов на странице

# --- API ViewSets ---
class ServiceViewSet(viewsets.ModelViewSet):
    """ API для Услуг (CRUD для админов/исполнителей, чтение для всех). """
    queryset = Service.objects.select_related('cost_calculator').all().order_by('name')
    serializer_class = ServiceSerializer
    permission_classes = [IsAdminOrExecutorOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['price', 'duration_hours']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at', 'duration_hours']
    ordering = ['name']

    def perform_create(self, serializer):
        """ Создаем Service и связанный CostCalculator. """
        service = serializer.save()
        CostCalculator.objects.create(
            service=service,
            base_price=service.price,
        )
        print(f"CostCalculator created for new service '{service.name}'") # Отладка

    def perform_update(self, serializer):
        """ Обновляем Service и связанный CostCalculator. """
        service = serializer.save()
        calc, created = CostCalculator.objects.update_or_create(
            service=service,
            defaults={'base_price': service.price}
        )
        if created:
             print(f"CostCalculator created during update for service '{service.name}'") # Отладка
        else:
             print(f"CostCalculator updated for service '{service.name}'") # Отладка

class ExecutorViewSet(viewsets.ReadOnlyModelViewSet):
    """API для просмотра Исполнителей."""
    queryset = Executor.objects.select_related('user').prefetch_related('services').all().order_by('user__username')
    serializer_class = ExecutorSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['specialization', 'experience_years', 'services__id'] 
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'specialization']
    ordering_fields = ['user__username', 'experience_years', 'created_at']
    ordering = ['user__username']

class OrderViewSet(viewsets.ModelViewSet):
    """API для Заказов (CRUD)."""
    serializer_class = OrderReadSerializer 
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status__status_name', 'service__id', 'executor__id'] 
    ordering_fields = ['created_at', 'scheduled_at', 'completed_at', 'service__price']
    ordering = ['-created_at']

    # Используем разные сериализаторы для чтения и записи
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return OrderWriteSerializer
        return OrderReadSerializer

    def get_queryset(self):
        """Показываем только заказы текущего пользователя (клиента или исполнителя)."""
        user = self.request.user
        if user.is_staff: # Админ видит все
            return Order.objects.select_related(
                'client', 'executor__user', 'service', 'status'
            ).all()
        # Фильтруем по клиенту ИЛИ исполнителю
        return Order.objects.select_related(
            'client', 'executor__user', 'service', 'status'
        ).filter(Q(client=user) | Q(executor__user=user)) # Q нужен для OR

    # Переопределяем perform_create (убедимся что client устанавливается)
    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated]) 
    def mark_as_processing(self, request, pk=None):
        order = self.get_object()
        # только исполнитель или админ могут менять статус 
        if not (request.user.is_staff or (order.executor and order.executor.user == request.user)):
             return Response({'detail': 'У вас нет прав для изменения статуса этого заказа.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            status_proc = OrderStatus.objects.get(status_name='processing')
            if order.status.status_name not in ['completed', 'cancelled']:
                order.status = status_proc
                order.completed_at = None
                order.save(update_fields=['status', 'completed_at'])
                serializer = self.get_serializer(order)
                return Response(serializer.data)
            else:
                 return Response({'error': 'Нельзя изменить статус выполненного или отмененного заказа'}, status=status.HTTP_400_BAD_REQUEST)
        except OrderStatus.DoesNotExist:
            return Response({'error': 'Статус "processing" не найден'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_as_completed(self, request, pk=None):
        order = self.get_object()
        if not (request.user.is_staff or (order.executor and order.executor.user == request.user)):
             return Response({'detail': 'У вас нет прав для изменения статуса этого заказа.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            status_completed = OrderStatus.objects.get(status_name='completed')
            if order.status.status_name not in ['completed', 'cancelled']:
                order.status = status_completed
                order.completed_at = timezone.now()
                order.save(update_fields=['status', 'completed_at'])
                serializer = self.get_serializer(order)
                return Response(serializer.data)
            else:
                 return Response({'error': 'Заказ уже выполнен или отменен'}, status=status.HTTP_400_BAD_REQUEST)
        except OrderStatus.DoesNotExist:
            return Response({'error': 'Статус "completed" не найден'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        order = self.get_object()
        # Права: Заказчик может отменить 'new' или 'processing'? 
        # Пример: Отменить может заказчик, если статус 'new'
        can_cancel = False
        if request.user == order.client and order.status.status_name in ['new']:
             can_cancel = True
        # Или если админ
        if request.user.is_staff:
            can_cancel = True

        if not can_cancel:
             return Response({'detail': 'Вы не можете отменить этот заказ на данном этапе.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            status_cancelled = OrderStatus.objects.get(status_name='cancelled')
            if order.status.status_name not in ['completed', 'cancelled']:
                order.status = status_cancelled
                order.completed_at = timezone.now()
                order.save(update_fields=['status', 'completed_at'])
                serializer = self.get_serializer(order)
                return Response(serializer.data)
            else:
                return Response({'error': 'Заказ уже выполнен или отменен'}, status=status.HTTP_400_BAD_REQUEST)
        except OrderStatus.DoesNotExist:
             return Response({'error': 'Статус "cancelled" не найден'}, status=status.HTTP_404_NOT_FOUND)


class NewsViewSet(viewsets.ModelViewSet):
    """ API для Новостей (CRUD для админов, чтение для всех). """
    queryset = News.objects.select_related('author').all().order_by('-published_at')
    serializer_class = NewsSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author__id']
    search_fields = ['title', 'content', 'author__username']
    ordering_fields = ['published_at', 'title']
    ordering = ['-published_at']

    def perform_create(self, serializer):
        """ Устанавливаем текущего пользователя (админа) как автора новости. """
        serializer.save(author=self.request.user)

class PortfolioViewSet(viewsets.ModelViewSet): # !!! Меняем на ModelViewSet !!!
     """ API для Портфолио (CRUD для владельца/админа, чтение для всех). """
     queryset = Portfolio.objects.select_related('executor__user').all().order_by('-uploaded_at')
     serializer_class = PortfolioSerializer
     permission_classes = [IsAdminOrExecutorOrReadOnly, IsPortfolioOwnerOrAdminOrReadOnly]
     pagination_class = StandardResultsSetPagination
     filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
     filterset_fields = ['executor__id']
     search_fields = ['title', 'description', 'executor__user__username']
     ordering_fields = ['uploaded_at', 'title']
     ordering = ['-uploaded_at']

     def perform_create(self, serializer):
         """ Устанавливаем текущего пользователя (исполнителя) как владельца портфолио. """
         user = self.request.user
         # Проверяем, является ли пользователь исполнителем
         if hasattr(user, 'executor_profile') and user.executor_profile:
             serializer.save(executor=user.executor_profile)
         elif user.is_staff:
             raise PermissionDenied("Администратор не может создавать портфолио без указания исполнителя.")
         else:
             # Если пользователь не исполнитель и не админ
             raise PermissionDenied("Только исполнители могут добавлять работы в портфолио.")

class ReviewViewSet(viewsets.ModelViewSet):
     """API для Отзывов (CRUD)."""
     queryset = Review.objects.select_related('user', 'executor__user', 'order').all().order_by('-created_at')
     serializer_class = ReviewSerializer
     # IsAuthenticatedOrReadOnly - гости видят, авторизованные могут создавать
     # IsOwnerOrReadOnly - редактировать/удалять может только автор отзыва
     permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
     pagination_class = StandardResultsSetPagination
     filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
     filterset_fields = ['executor__id', 'order__id', 'rating', 'user__id'] # ?executor__id=1&rating=5
     ordering_fields = ['created_at', 'rating']
     ordering = ['-created_at']

class OrderStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """API для получения списка Статусов Заказов."""
    queryset = OrderStatus.objects.all().order_by('pk')
    serializer_class = OrderStatusSerializer
    permission_classes = [permissions.AllowAny] # Статусы доступны всем

class CartViewSet(mixins.RetrieveModelMixin, # Получить корзину (GET /cart/)
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    """
    API для управления корзиной текущего пользователя.
    Доступ: /studio/api/cart/ (GET, POST, DELETE?)
           /studio/api/cart/items/ (POST для добавления)
           /studio/api/cart/items/{item_pk}/ (PUT, PATCH, DELETE для изменения/удаления)
    """
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated, IsCartOwner] # Только владелец

    def get_queryset(self):
        """Возвращает корзину текущего пользователя."""
        user = self.request.user
        return Cart.objects.filter(user=user).prefetch_related('items__service')

    def get_object(self):
        """Получает или создает корзину для текущего пользователя."""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        # Проверяем права доступа 
        self.check_object_permissions(self.request, cart)
        return cart

    def list(self, request, *args, **kwargs):
        """Переопределяем list, чтобы всегда возвращать одну корзину пользователя."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # retrieve работает из коробки через get_object

    @action(detail=False, methods=['post'], url_path='items', serializer_class=CartItemSerializer)
    def add_item(self, request):
        """Добавляет товар (услугу) в корзину или увеличивает количество."""
        cart = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Получаем ID услуги из validated_data
        service_id = serializer.validated_data.get('service_id') # Или может называться 'service' если source отработал
        if not service_id and 'service' in serializer.validated_data:
            # Если ключ 'service' есть, но это ID, а не объект
             if isinstance(serializer.validated_data['service'], int):
                 service_id = serializer.validated_data['service']
             # Если вдруг там объект Service 
             elif isinstance(serializer.validated_data['service'], Service):
                 service_id = serializer.validated_data['service'].pk

        # Если service_id все еще не найден, это ошибка в запросе или сериализаторе
        if not service_id:
             service_id = request.data.get('service_id')
             if not service_id:
                 return Response({'service_id': 'Это поле обязательно.'}, status=status.HTTP_400_BAD_REQUEST)
             try:
                 service_id = int(service_id)
             except (ValueError, TypeError):
                  return Response({'service_id': 'Неверный ID услуги.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
             service_object = Service.objects.get(pk=service_id)
        except Service.DoesNotExist:
             return Response({'service_id': 'Услуга с таким ID не найдена.'}, status=status.HTTP_404_NOT_FOUND)
        quantity = serializer.validated_data.get('quantity', 1)

        # есть ли уже такой товар в корзине
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            service=service_object,
            defaults={'quantity': quantity}
        )

        if not created:
            # увеличиваем количество
            cart_item.quantity = F('quantity') + quantity # Используем F
            cart_item.save(update_fields=['quantity'])
            cart_item.refresh_from_db() # Обновляем объект после F
            cart.save()
            cart_serializer = CartSerializer(cart, context=self.get_serializer_context())
            return Response(cart_serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        else:
             cart.save()
             cart_serializer = CartSerializer(cart, context=self.get_serializer_context())
        return Response(cart_serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

    @action(detail=False, methods=['patch'], url_path='items/(?P<item_pk>[^/.]+)', serializer_class=CartItemSerializer)
    def update_item_quantity(self, request, item_pk=None):
        print("--- update_item_quantity ---")
        print("Request data:", request.data)
        print("Item PK:", item_pk)
        cart = self.get_object()
        cart_item = get_object_or_404(CartItem, pk=item_pk, cart=cart)

        try:
            # Пытаемся получить и преобразовать quantity
            new_quantity = int(request.data.get('quantity'))
            if new_quantity <= 0:
                raise ValueError("Количество должно быть положительным.") 

            cart_item.quantity = new_quantity
            cart_item.save(update_fields=['quantity']) # Обновляем только quantity
            cart.save() # Обновляем updated_at корзины

            cart_serializer = CartSerializer(cart, context=self.get_serializer_context())
            return Response(cart_serializer.data)

        except (ValueError, TypeError, KeyError):
            # Если quantity нет, не число или <= 0
             return Response({'quantity': 'Ожидается целое положительное число.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
             # Ловим другие возможные ошибки
             print(f"Error updating cart item quantity: {e}")
             return Response({'detail': 'Внутренняя ошибка сервера при обновлении количества.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['delete'], url_path='items/(?P<item_pk>[^/.]+)')
    def remove_item(self, request, item_pk=None):
        """ Удаляет товар из корзины. """
        cart = self.get_object()
        cart_item = get_object_or_404(CartItem, pk=item_pk, cart=cart)
        cart_item.delete()
        cart.save()
        return Response(status=status.HTTP_204_NO_CONTENT) # Успешное удаление

    @action(detail=False, methods=['delete'], url_path='clear') # Используем detail=False, работаем с корзиной текущего пользователя
    def clear_cart(self, request):
        """Очищает корзину пользователя."""
        cart = self.get_object()
        cart.items.all().delete()
        cart.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class MessageViewSet(mixins.CreateModelMixin, # Создать (отправить)
                     mixins.ListModelMixin, # Список входящих/исходящих
                     mixins.RetrieveModelMixin, # Просмотреть одно сообщение
                     mixins.DestroyModelMixin, # Удалить сообщение? (Обычно нет)
                     viewsets.GenericViewSet):
    """API для просмотра и отправки сообщений."""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsMessageParticipantOrReadOnly] # Только участники чата
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_read', 'sender__id', 'receiver__id'] 
    ordering_fields = ['sent_at']
    ordering = ['-sent_at']

    def get_queryset(self):
        """Показываем только сообщения, где пользователь - отправитель или получатель."""
        user = self.request.user
        return Message.objects.filter(Q(sender=user) | Q(receiver=user)).select_related('sender', 'receiver')

    # Можно добавить action для пометки сообщения как прочитанного
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_as_read(self, request, pk=None):
        message = self.get_object()
        if message.receiver == request.user and not message.is_read:
            message.is_read = True
            message.save(update_fields=['is_read'])
            serializer = self.get_serializer(message)
            return Response(serializer.data)
        elif message.receiver != request.user:
             return Response({'detail': 'Вы не получатель этого сообщения.'}, status=status.HTTP_403_FORBIDDEN)
        else: # Уже прочитано
             serializer = self.get_serializer(message)
             return Response(serializer.data) # Просто возвращаем данные

class UserProfileView(generics.RetrieveUpdateAPIView):
    """API для получения и обновления профиля текущего пользователя."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user



def service_list(request):
    services_qs = Service.objects.select_related('cost_calculator') \
                                .prefetch_related('orders', 'executors__user') \
                                .filter(name__icontains='')
    min_price = request.GET.get('min_price')
    if min_price:
        try: services_qs = services_qs.filter(price__gte=float(min_price))
        except ValueError: messages.error(request, "Некорректное значение для минимальной цены.")
    search_query = request.GET.get('search', '')
    if search_query:
        services_qs = services_qs.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))
    services_with_duration = services_qs.annotate_duration_info().order_by('-created_at')
    context = {'services': services_with_duration, 'search_query': search_query, 'min_price': min_price,}
    return render(request, 'app_studio/service_list.html', context)

def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('client', 'executor__user', 'service', 'status'), pk=pk)
    related_orders = Order.objects.filter(client=order.client) \
                                  .exclude(status__status_name='cancelled') \
                                  .exclude(pk=order.pk) \
                                  .select_related('service', 'status') \
                                  .order_by('-created_at')[:5]
    context = {'order': order, 'related_orders': related_orders,}
    return render(request, 'app_studio/order_detail.html', context)

# --- Заглушки для get_absolute_url ---
def user_detail_placeholder(request, pk): # Заглушка для CustomUser.get_absolute_url
    user = get_object_or_404(CustomUser, pk=pk)
    return HttpResponse(f"Профиль пользователя (заглушка): {user.username} (PK={pk})")

def executor_detail_placeholder(request, pk): # Заглушка (если get_absolute_url не ведет на API)
    executor = get_object_or_404(Executor.objects.select_related('user'), pk=pk)
    return HttpResponse(f"Профиль исполнителя (заглушка): {executor.user.username} (PK={pk})")

def news_detail_placeholder(request, pk): # Заглушка (если get_absolute_url не ведет на API)
    news_item = get_object_or_404(News.objects.select_related('author'), pk=pk)
    return HttpResponse(f"Новость (заглушка): {news_item.title} (PK={pk})")

def cart_detail_placeholder(request): # Заглушка (если get_absolute_url не ведет на API)
    if not request.user.is_authenticated: return redirect('login')
    cart, created = Cart.objects.get_or_create(user=request.user)
    return HttpResponse(f"Корзина пользователя (заглушка): {request.user.username} (PK={cart.pk})")

def portfolio_detail_placeholder(request, pk): # Заглушка (если get_absolute_url не ведет на API)
    portfolio_item = get_object_or_404(Portfolio.objects.select_related('executor__user'), pk=pk)
    return HttpResponse(f"Работа в портфолио (заглушка): {portfolio_item.title} (PK={pk})")

def service_detail(request, pk): # Заглушка (если get_absolute_url не ведет на API)
    service = get_object_or_404(Service, pk=pk)
    return HttpResponse(f"Детали услуги (заглушка): {service.name} (PK={pk})")