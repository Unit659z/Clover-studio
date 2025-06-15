from typing import Any, Type, Optional, Union, List, Dict, Callable
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, HttpRequest, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Avg, Sum, F, Q, QuerySet as DjangoQuerySet
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.contrib.auth import update_session_auth_hash
from django.conf import settings 

from rest_framework import views, permissions, status, generics, serializers as drf_serializers
from rest_framework.request import Request 
from rest_framework.response import Response
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend

from .permissions import (
    IsOwnerOrReadOnly, IsCartOwner, IsMessageParticipantOrReadOnly,
    IsAdminOrExecutorOrReadOnly, IsPortfolioOwnerOrAdminOrReadOnly, IsAdminOrReadOnly
)
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


def trigger_sentry_error(request: HttpRequest) -> HttpResponse:
    """
    Тестовый view для генерации исключения ZeroDivisionError.
    Используется для проверки интеграции с Sentry.

    Args:
        request: Объект HttpRequest.

    Returns:
        HttpResponse: Сообщение, которое не будет достигнуто из-за ошибки.
    """
    division_by_zero: int = 1 / 0
    return HttpResponse("Эта страница намеренно вызывает ошибку для теста Sentry.")

class PasswordChangeView(generics.GenericAPIView):
    """
    API View для смены пароля аутентифицированным пользователем.
    """
    serializer_class: Type[PasswordChangeSerializer] = PasswordChangeSerializer
    permission_classes: List[Type[permissions.BasePermission]] = [permissions.IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Обрабатывает POST-запрос для смены пароля.

        Args:
            request: Объект DRF Request.
            *args: Дополнительные позиционные аргументы.
            **kwargs: Дополнительные именованные аргументы.

        Returns:
            Response: Ответ DRF с сообщением об успехе или ошибками валидации.
        """
        serializer: PasswordChangeSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: CustomUser = request.user
        user.set_password(serializer.validated_data['new_password1'])
        user.save()

        update_session_auth_hash(request, user)

        return Response({"detail": "Пароль успешно изменен."}, status=status.HTTP_200_OK)

class RegisterView(generics.CreateAPIView):
    """
    API View для регистрации новых пользователей.

    Автоматически аутентифицирует пользователя после успешной регистрации,
    если 'django.contrib.auth.backends.ModelBackend' присутствует в AUTHENTICATION_BACKENDS.
    """
    queryset: DjangoQuerySet[CustomUser] = CustomUser.objects.all()
    permission_classes: List[Type[permissions.BasePermission]] = [permissions.AllowAny]
    serializer_class: Type[RegisterSerializer] = RegisterSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Обрабатывает POST-запрос для создания нового пользователя.

        Args:
            request: Объект DRF Request.
            *args: Дополнительные позиционные аргументы.
            **kwargs: Дополнительные именованные аргументы.

        Returns:
            Response: Ответ DRF с данными созданного пользователя (статус 201) или ошибками валидации.
        """
        serializer: RegisterSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user: CustomUser = serializer.save()

        backend_path: str = 'django.contrib.auth.backends.ModelBackend'

        if backend_path in settings.AUTHENTICATION_BACKENDS:
            user.backend = backend_path
            django_login(request, user)
            print(f"User {user.username} automatically logged in after registration.")
        else:
            print(f"ERROR: Specified backend '{backend_path}' not found in AUTHENTICATION_BACKENDS. User not logged in.")

        user_data_serializer: UserSerializer = UserSerializer(user, context=self.get_serializer_context())
        headers: Dict[str, str] = self.get_success_headers(user_data_serializer.data)
        return Response(user_data_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class LoginView(views.APIView):
    """
    API View для входа пользователя по имени пользователя или email и паролю.

    Устанавливает sessionid cookie при успешном входе.
    Использует кастомный бэкенд EmailOrUsernameBackend.
    """
    permission_classes: List[Type[permissions.BasePermission]] = [permissions.AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Обрабатывает POST-запрос для аутентификации пользователя.

        Ожидает 'identifier' (username или email) и 'password' в теле запроса.

        Args:
            request: Объект DRF Request.
            *args: Дополнительные позиционные аргументы.
            **kwargs: Дополнительные именованные аргументы.

        Returns:
            Response: Ответ DRF с данными пользователя при успехе или ошибкой аутентификации.
        """
        identifier: Optional[str] = request.data.get('identifier')
        password: Optional[str] = request.data.get('password')

        if not identifier or not password:
            return Response(
                {'detail': 'Необходимо указать имя пользователя/email и пароль.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user: Optional[CustomUser] = authenticate(request, username=identifier, password=password)

        if user is not None:
            if not user.is_active:
                 return Response(
                     {'detail': 'Аккаунт пользователя неактивен.'},
                     status=status.HTTP_401_UNAUTHORIZED
                 )

            django_login(request, user)
            serializer: UserSerializer = UserSerializer(user, context={'request': request})
            return Response(serializer.data)
        else:
            return Response(
                {'detail': 'Неверные учетные данные или аккаунт неактивен.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

class LogoutView(views.APIView):
    """
    API View для выхода пользователя.

    Удаляет сессию пользователя. Требует аутентификации.
    """
    permission_classes: List[Type[permissions.BasePermission]] = [permissions.IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Обрабатывает POST-запрос для выхода пользователя.

        Args:
            request: Объект DRF Request.
            *args: Дополнительные позиционные аргументы.
            **kwargs: Дополнительные именованные аргументы.

        Returns:
            Response: Ответ DRF с сообщением об успешном выходе.
        """
        django_logout(request._request) # django_logout ожидает HttpRequest
        return Response(
            {'detail': 'Выход выполнен успешно.'},
            status=status.HTTP_200_OK
        )

class SessionStatusView(views.APIView):
    """
    Проверяет, аутентифицирован ли пользователь по сессии.

    Возвращает данные пользователя, если аутентифицирован, иначе 401/403.
    Гарантированно устанавливает CSRF cookie при GET запросе.
    """
    permission_classes: List[Type[permissions.BasePermission]] = [permissions.IsAuthenticated]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Обрабатывает GET-запрос для проверки статуса сессии.

        Args:
            request: Объект DRF Request.
            *args: Дополнительные позиционные аргументы.
            **kwargs: Дополнительные именованные аргументы.

        Returns:
            Response: Ответ DRF с сериализованными данными текущего пользователя.
        """
        serializer: UserSerializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API для получения и обновления профиля текущего аутентифицированного пользователя.
    """
    serializer_class: Type[UserSerializer] = UserSerializer
    permission_classes: List[Type[permissions.BasePermission]] = [permissions.IsAuthenticated]

    def get_object(self) -> CustomUser:
        """
        Возвращает объект текущего пользователя.

        Returns:
            CustomUser: Экземпляр модели текущего пользователя.
        """
        return self.request.user # type: ignore

class GetCSRFTokenView(views.APIView):
    """
    API View для получения CSRF cookie.
    Полезно для фронтенд-приложений для инициализации CSRF-защиты.
    """
    permission_classes: List[Type[permissions.BasePermission]] = [permissions.AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Обрабатывает GET-запрос и устанавливает CSRF cookie.

        Args:
            request: Объект DRF Request.
            *args: Дополнительные позиционные аргументы.
            **kwargs: Дополнительные именованные аргументы.

        Returns:
            Response: Ответ DRF с сообщением об установке cookie и значением токена.
        """
        return Response({'detail': 'CSRF cookie set.', 'csrfToken': get_token(request._request)}) # get_token ожидает HttpRequest

class StandardResultsSetPagination(PageNumberPagination):
    """
    Стандартный класс пагинации для ViewSet'ов.
    Определяет количество элементов на странице и максимальное их количество.
    """
    page_size: int = 10
    page_size_query_param: str = 'page_size'
    max_page_size: int = 100

class ServiceViewSet(viewsets.ModelViewSet):
    """
    API эндпоинт для управления Услугами.

    Предоставляет CRUD операции. Создание/изменение/удаление доступно
    администраторам или пользователям с профилем исполнителя.
    Чтение доступно всем.
    """
    queryset: DjangoQuerySet[Service] = Service.objects.select_related('cost_calculator').all().order_by('name')
    serializer_class: Type[ServiceSerializer] = ServiceSerializer
    permission_classes: List[Type[permissions.BasePermission]] = [IsAdminOrExecutorOrReadOnly]
    pagination_class: Type[PageNumberPagination] = StandardResultsSetPagination
    filter_backends: List[Any] = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields: List[str] = ['price', 'duration_hours']
    search_fields: List[str] = ['name', 'description']
    ordering_fields: List[str] = ['name', 'price', 'created_at', 'duration_hours']
    ordering: List[str] = ['name']

    def perform_create(self, serializer: ServiceSerializer) -> None:
        """
        Выполняется при создании нового объекта Service.
        Автоматически создает связанный объект CostCalculator.

        Args:
            serializer: Сериализатор с валидными данными для создания услуги.
        """
        service: Service = serializer.save()
        CostCalculator.objects.create(
            service=service,
            base_price=service.price,
        )
        print(f"CostCalculator created for new service '{service.name}'")

    def perform_update(self, serializer: ServiceSerializer) -> None:
        """
        Выполняется при обновлении объекта Service.
        Обновляет или создает связанный объект CostCalculator.

        Args:
            serializer: Сериализатор с валидными данными для обновления услуги.
        """
        service: Service = serializer.save()
        calc, created = CostCalculator.objects.update_or_create(
            service=service,
            defaults={'base_price': service.price}
        )
        if created:
             print(f"CostCalculator created during update for service '{service.name}'")
        else:
             print(f"CostCalculator updated for service '{service.name}'")

class ExecutorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API эндпоинт для просмотра профилей Исполнителей.
    Предоставляет только операции чтения. Доступно всем.
    """
    queryset: DjangoQuerySet[Executor] = Executor.objects.select_related('user').prefetch_related('services').all().order_by('user__username')
    serializer_class: Type[ExecutorSerializer] = ExecutorSerializer
    permission_classes: List[Type[permissions.BasePermission]] = [permissions.AllowAny]
    pagination_class: Type[PageNumberPagination] = StandardResultsSetPagination
    filter_backends: List[Any] = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields: Dict[str, List[str]] = {'specialization': ['exact', 'icontains'], 'experience_years': ['exact', 'gte', 'lte'], 'services__id': ['exact']}
    search_fields: List[str] = ['user__username', 'user__first_name', 'user__last_name', 'specialization']
    ordering_fields: List[str] = ['user__username', 'experience_years', 'created_at']
    ordering: List[str] = ['user__username']

class OrderViewSet(viewsets.ModelViewSet):
    """
    API эндпоинт для управления Заказами.
    Предоставляет CRUD операции. Доступно аутентифицированным пользователям.
    Пользователи видят только свои заказы (как клиенты или исполнители),
    администраторы видят все заказы.
    """
    permission_classes: List[Type[permissions.BasePermission]] = [permissions.IsAuthenticated]
    pagination_class: Type[PageNumberPagination] = StandardResultsSetPagination
    filter_backends: List[Any] = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields: List[str] = ['status__status_name', 'service__id', 'executor__id']
    ordering_fields: List[str] = ['created_at', 'scheduled_at', 'completed_at', 'service__price']
    ordering: List[str] = ['-created_at']

    def get_serializer_class(self) -> Type[Union[OrderReadSerializer, OrderWriteSerializer]]:
        """
        Возвращает класс сериализатора в зависимости от действия.
        Использует OrderWriteSerializer для создания/обновления, OrderReadSerializer для остального.
        """
        if self.action in ['create', 'update', 'partial_update']:
            return OrderWriteSerializer
        return OrderReadSerializer

    def get_queryset(self) -> DjangoQuerySet[Order]:
        """
        Возвращает QuerySet заказов, отфильтрованный для текущего пользователя.
        Администраторы видят все заказы. Клиенты/исполнители видят только свои.
        """
        user: CustomUser = self.request.user # type: ignore
        if user.is_staff:
            return Order.objects.select_related(
                'client', 'executor__user', 'service', 'status'
            ).all()
        return Order.objects.select_related(
            'client', 'executor__user', 'service', 'status'
        ).filter(Q(client=user) | Q(executor__user=user))

    def perform_create(self, serializer: OrderWriteSerializer) -> None:
        """
        Выполняется при создании нового Заказа.
        Клиент устанавливается автоматически.

        Args:
            serializer: Сериализатор с валидными данными для создания заказа.
        """
        serializer.save() # client=self.request.user устанавливается в сериализаторе

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_as_processing(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Action для установки статуса заказа "В обработке".
        Доступно исполнителю заказа или администратору.

        Args:
            request: Объект DRF Request.
            pk: Первичный ключ заказа.

        Returns:
            Response: Сериализованные данные обновленного заказа или сообщение об ошибке.
        """
        order: Order = self.get_object() # type: ignore
        user: CustomUser = request.user # type: ignore
        if not (user.is_staff or (order.executor and order.executor.user == user)):
             return Response({'detail': 'У вас нет прав для изменения статуса этого заказа.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            status_proc: OrderStatus = OrderStatus.objects.get(status_name='processing')
            if order.status and order.status.status_name not in ['completed', 'cancelled']:
                order.status = status_proc
                order.completed_at = None
                order.save(update_fields=['status', 'completed_at'])
                serializer: OrderReadSerializer = self.get_serializer(order)
                return Response(serializer.data)
            else:
                 return Response({'error': 'Нельзя изменить статус выполненного или отмененного заказа'}, status=status.HTTP_400_BAD_REQUEST)
        except OrderStatus.DoesNotExist:
            return Response({'error': 'Статус "processing" не найден'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_as_completed(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Action для установки статуса заказа "Выполнен".
        Доступно исполнителю заказа или администратору.

        Args:
            request: Объект DRF Request.
            pk: Первичный ключ заказа.

        Returns:
            Response: Сериализованные данные обновленного заказа или сообщение об ошибке.
        """
        order: Order = self.get_object() # type: ignore
        user: CustomUser = request.user # type: ignore
        if not (user.is_staff or (order.executor and order.executor.user == user)):
             return Response({'detail': 'У вас нет прав для изменения статуса этого заказа.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            status_completed: OrderStatus = OrderStatus.objects.get(status_name='completed')
            if order.status and order.status.status_name not in ['completed', 'cancelled']:
                order.status = status_completed
                order.completed_at = timezone.now()
                order.save(update_fields=['status', 'completed_at'])
                serializer: OrderReadSerializer = self.get_serializer(order)
                return Response(serializer.data)
            else:
                 return Response({'error': 'Заказ уже выполнен или отменен'}, status=status.HTTP_400_BAD_REQUEST)
        except OrderStatus.DoesNotExist:
            return Response({'error': 'Статус "completed" не найден'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Action для отмены заказа.
        Доступно клиенту (если заказ в статусе 'new') или администратору.

        Args:
            request: Объект DRF Request.
            pk: Первичный ключ заказа.

        Returns:
            Response: Сериализованные данные обновленного заказа или сообщение об ошибке.
        """
        order: Order = self.get_object() 
        user: CustomUser = request.user 
        can_cancel: bool = False
        if order.status and user == order.client and order.status.status_name in ['new']:
             can_cancel = True
        if user.is_staff:
            can_cancel = True

        if not can_cancel:
             return Response({'detail': 'Вы не можете отменить этот заказ на данном этапе.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            status_cancelled: OrderStatus = OrderStatus.objects.get(status_name='cancelled')
            if order.status and order.status.status_name not in ['completed', 'cancelled']:
                order.status = status_cancelled
                order.completed_at = timezone.now() # Или None, в зависимости от логики
                order.save(update_fields=['status', 'completed_at'])
                serializer: OrderReadSerializer = self.get_serializer(order)
                return Response(serializer.data)
            else:
                return Response({'error': 'Заказ уже выполнен или отменен'}, status=status.HTTP_400_BAD_REQUEST)
        except OrderStatus.DoesNotExist:
             return Response({'error': 'Статус "cancelled" не найден'}, status=status.HTTP_404_NOT_FOUND)


class NewsViewSet(viewsets.ModelViewSet):
    """
    API эндпоинт для управления Новостями.
    CRUD доступен администраторам, чтение - всем.
    """
    queryset: DjangoQuerySet[News] = News.objects.select_related('author').all().order_by('-published_at')
    serializer_class: Type[NewsSerializer] = NewsSerializer
    permission_classes: List[Type[permissions.BasePermission]] = [IsAdminOrReadOnly]
    pagination_class: Type[PageNumberPagination] = StandardResultsSetPagination
    filter_backends: List[Any] = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields: List[str] = ['author__id']
    search_fields: List[str] = ['title', 'content', 'author__username']
    ordering_fields: List[str] = ['published_at', 'title']
    ordering: List[str] = ['-published_at']

    def perform_create(self, serializer: NewsSerializer) -> None:
        """
        Выполняется при создании новой Новости.
        Автоматически устанавливает текущего пользователя (администратора) как автора.

        Args:
            serializer: Сериализатор с валидными данными для создания новости.
        """
        serializer.save(author=self.request.user)

class PortfolioViewSet(viewsets.ModelViewSet):
     """
     API эндпоинт для управления работами в Портфолио.
     CRUD доступен владельцу портфолио (исполнителю) или администратору.
     Чтение доступно всем.
     """
     queryset: DjangoQuerySet[Portfolio] = Portfolio.objects.select_related('executor__user').all().order_by('-uploaded_at')
     serializer_class: Type[PortfolioSerializer] = PortfolioSerializer
     permission_classes: List[Type[permissions.BasePermission]] = [IsAdminOrExecutorOrReadOnly, IsPortfolioOwnerOrAdminOrReadOnly]
     pagination_class: Type[PageNumberPagination] = StandardResultsSetPagination
     filter_backends: List[Any] = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
     filterset_fields: List[str] = ['executor__id']
     search_fields: List[str] = ['title', 'description', 'executor__user__username']
     ordering_fields: List[str] = ['uploaded_at', 'title']
     ordering: List[str] = ['-uploaded_at']

     def perform_create(self, serializer: PortfolioSerializer) -> None:
         """
         Выполняется при создании новой работы в Портфолио.
         Устанавливает текущего пользователя (если он исполнитель) как владельца.

         Args:
             serializer: Сериализатор с валидными данными.

         Raises:
             PermissionDenied: Если пользователь не исполнитель или администратор пытается создать без указания исполнителя.
         """
         user: CustomUser = self.request.user # type: ignore
         if hasattr(user, 'executor_profile') and user.executor_profile: # type: ignore
             serializer.save(executor=user.executor_profile) # type: ignore
         elif user.is_staff:
             raise PermissionDenied("Администратор не может создавать портфолио без указания исполнителя.")
         else:
             raise PermissionDenied("Только исполнители могут добавлять работы в портфолио.")

class ReviewViewSet(viewsets.ModelViewSet):
     """
     API эндпоинт для управления Отзывами.
     Аутентифицированные пользователи могут создавать отзывы.
     Редактировать/удалять может только автор отзыва.
     Чтение доступно всем.
     """
     queryset: DjangoQuerySet[Review] = Review.objects.select_related('user', 'executor__user', 'order').all().order_by('-created_at')
     serializer_class: Type[ReviewSerializer] = ReviewSerializer
     permission_classes: List[Type[permissions.BasePermission]] = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
     pagination_class: Type[PageNumberPagination] = StandardResultsSetPagination
     filter_backends: List[Any] = [DjangoFilterBackend, filters.OrderingFilter]
     filterset_fields: List[str] = ['executor__id', 'order__id', 'rating', 'user__id']
     ordering_fields: List[str] = ['created_at', 'rating']
     ordering: List[str] = ['-created_at']

class OrderStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API эндпоинт для получения списка Статусов Заказов.
    Доступно всем. Только чтение.
    """
    queryset: DjangoQuerySet[OrderStatus] = OrderStatus.objects.all().order_by('pk')
    serializer_class: Type[OrderStatusSerializer] = OrderStatusSerializer
    permission_classes: List[Type[permissions.BasePermission]] = [permissions.AllowAny]

class CartViewSet(mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    """
    API для управления корзиной текущего пользователя.

    Предоставляет эндпоинты для получения корзины, добавления,
    обновления количества и удаления товаров из корзины, а также очистки корзины.
    Доступно только аутентифицированным владельцам корзины.
    """
    serializer_class: Type[CartSerializer] = CartSerializer
    permission_classes: List[Type[permissions.BasePermission]] = [permissions.IsAuthenticated, IsCartOwner]

    def get_queryset(self) -> DjangoQuerySet[Cart]:
        """
        Возвращает QuerySet с корзиной текущего пользователя.
        """
        user: CustomUser = self.request.user # type: ignore
        return Cart.objects.filter(user=user).prefetch_related('items__service')

    def get_object(self) -> Cart:
        """
        Получает или создает корзину для текущего пользователя.
        Проверяет права доступа к объекту корзины.

        Returns:
            Cart: Объект корзины текущего пользователя.
        """
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        self.check_object_permissions(self.request, cart)
        return cart

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Переопределенный метод list для возврата одной корзины пользователя.

        Args:
            request: Объект DRF Request.
            *args: Дополнительные позиционные аргументы.
            **kwargs: Дополнительные именованные аргументы.

        Returns:
            Response: Сериализованные данные корзины пользователя.
        """
        instance: Cart = self.get_object()
        serializer: CartSerializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='items', serializer_class=CartItemSerializer)
    def add_item(self, request: Request) -> Response:
        """
        Action для добавления товара (услуги) в корзину или увеличения количества.

        Args:
            request: Объект DRF Request. Ожидает 'service_id' и опционально 'quantity' в теле.

        Returns:
            Response: Сериализованные данные обновленной корзины или сообщение об ошибке.
        """
        cart: Cart = self.get_object()
        serializer: CartItemSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service_id_from_serializer: Optional[Union[int, Service]] = serializer.validated_data.get('service') # type: ignore
        service_id: Optional[int] = None

        if isinstance(service_id_from_serializer, Service):
            service_id = service_id_from_serializer.pk
        elif isinstance(service_id_from_serializer, int):
            service_id = service_id_from_serializer
        
        if not service_id: # Если service_id не был получен из serializer.validated_data['service'] (из-за source)
             raw_service_id: Any = request.data.get('service_id')
             if not raw_service_id:
                 return Response({'service_id': 'Это поле обязательно.'}, status=status.HTTP_400_BAD_REQUEST)
             try:
                 service_id = int(raw_service_id)
             except (ValueError, TypeError):
                  return Response({'service_id': 'Неверный ID услуги.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
             service_object: Service = Service.objects.get(pk=service_id)
        except Service.DoesNotExist:
             return Response({'service_id': 'Услуга с таким ID не найдена.'}, status=status.HTTP_404_NOT_FOUND)
        
        quantity: int = serializer.validated_data.get('quantity', 1)

        cart_item: CartItem
        created: bool
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            service=service_object,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity = F('quantity') + quantity
            cart_item.save(update_fields=['quantity'])
            cart_item.refresh_from_db()
        
        cart.save() # Обновляем updated_at корзины
        cart_serializer: CartSerializer = CartSerializer(cart, context=self.get_serializer_context())
        return Response(cart_serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


    @action(detail=False, methods=['patch'], url_path=r'items/(?P<item_pk>[^/.]+)', serializer_class=CartItemSerializer)
    def update_item_quantity(self, request: Request, item_pk: Optional[str] = None) -> Response:
        """
        Action для обновления количества товара в корзине.

        Args:
            request: Объект DRF Request. Ожидает 'quantity' в теле.
            item_pk: Первичный ключ элемента корзины (CartItem).

        Returns:
            Response: Сериализованные данные обновленной корзины или сообщение об ошибке.
        """
        cart: Cart = self.get_object()
        cart_item: CartItem = get_object_or_404(CartItem, pk=item_pk, cart=cart)

        try:
            new_quantity_raw: Any = request.data.get('quantity')
            if new_quantity_raw is None:
                 raise KeyError("Отсутствует поле 'quantity'.")
            new_quantity: int = int(new_quantity_raw)
            if new_quantity <= 0:
                raise ValueError("Количество должно быть положительным.")

            cart_item.quantity = new_quantity
            cart_item.save(update_fields=['quantity'])
            cart.save()

            cart_serializer: CartSerializer = CartSerializer(cart, context=self.get_serializer_context())
            return Response(cart_serializer.data)

        except (ValueError, TypeError, KeyError) as e:
             return Response({'quantity': f'Ожидается целое положительное число. Ошибка: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
             print(f"Error updating cart item quantity: {e}")
             return Response({'detail': 'Внутренняя ошибка сервера при обновлении количества.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['delete'], url_path=r'items/(?P<item_pk>[^/.]+)')
    def remove_item(self, request: Request, item_pk: Optional[str] = None) -> Response:
        """
        Action для удаления товара из корзины.

        Args:
            request: Объект DRF Request.
            item_pk: Первичный ключ элемента корзины (CartItem).

        Returns:
            Response: Статус 204 No Content при успехе.
        """
        cart: Cart = self.get_object()
        cart_item: CartItem = get_object_or_404(CartItem, pk=item_pk, cart=cart)
        cart_item.delete()
        cart.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['delete'], url_path='clear')
    def clear_cart(self, request: Request) -> Response:
        """
        Action для полной очистки корзины пользователя.

        Args:
            request: Объект DRF Request.

        Returns:
            Response: Статус 204 No Content при успехе.
        """
        cart: Cart = self.get_object()
        cart.items.all().delete()
        cart.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class MessageViewSet(mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    """
    API эндпоинт для просмотра и отправки личных сообщений.
    Доступно только аутентифицированным участникам переписки.
    """
    serializer_class: Type[MessageSerializer] = MessageSerializer
    permission_classes: List[Type[permissions.BasePermission]] = [permissions.IsAuthenticated, IsMessageParticipantOrReadOnly]
    pagination_class: Type[PageNumberPagination] = StandardResultsSetPagination
    filter_backends: List[Any] = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields: List[str] = ['is_read', 'sender__id', 'receiver__id']
    ordering_fields: List[str] = ['sent_at']
    ordering: List[str] = ['-sent_at']

    def get_queryset(self) -> DjangoQuerySet[Message]:
        """
        Возвращает QuerySet сообщений, где текущий пользователь является отправителем или получателем.
        """
        user: CustomUser = self.request.user # type: ignore
        return Message.objects.filter(Q(sender=user) | Q(receiver=user)).select_related('sender', 'receiver')

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_as_read(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Action для пометки сообщения как прочитанного.
        Доступно только получателю сообщения.

        Args:
            request: Объект DRF Request.
            pk: Первичный ключ сообщения.

        Returns:
            Response: Сериализованные данные обновленного сообщения или сообщение об ошибке.
        """
        message: Message = self.get_object() # type: ignore
        user: CustomUser = request.user # type: ignore
        if message.receiver == user and not message.is_read:
            message.is_read = True
            message.save(update_fields=['is_read'])
            serializer: MessageSerializer = self.get_serializer(message)
            return Response(serializer.data)
        elif message.receiver != user:
             return Response({'detail': 'Вы не получатель этого сообщения.'}, status=status.HTTP_403_FORBIDDEN)
        else:
             serializer: MessageSerializer = self.get_serializer(message)
             return Response(serializer.data)


def service_list(request: HttpRequest) -> HttpResponse:
    """
    Отображает список услуг (пример старой Django view, не API).
    Поддерживает фильтрацию по минимальной цене и поиск.

    Args:
        request: Объект HttpRequest.

    Returns:
        HttpResponse: Рендеринг HTML-шаблона со списком услуг.
    """
    services_qs: DjangoQuerySet[Service] = Service.objects.select_related('cost_calculator') \
                                .prefetch_related('orders', 'executors__user') \
                                .filter(name__icontains='') # Изначально пустой поиск или базовая фильтрация
    
    min_price_str: Optional[str] = request.GET.get('min_price')
    if min_price_str:
        try:
            min_price_float: float = float(min_price_str)
            services_qs = services_qs.filter(price__gte=min_price_float)
        except ValueError:
            messages.error(request, "Некорректное значение для минимальной цены.")

    search_query: str = request.GET.get('search', '')
    if search_query:
        services_qs = services_qs.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))

    services_with_duration: DjangoQuerySet[Service] = services_qs.annotate_duration_info().order_by('-created_at') # type: ignore
    
    context: Dict[str, Any] = {
        'services': services_with_duration,
        'search_query': search_query,
        'min_price': min_price_str,
    }
    return render(request, 'app_studio/service_list.html', context)

def order_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Отображает детальную информацию о заказе (пример старой Django view, не API).

    Args:
        request: Объект HttpRequest.
        pk: Первичный ключ заказа.

    Returns:
        HttpResponse: Рендеринг HTML-шаблона с деталями заказа.
    """
    order: Order = get_object_or_404(
        Order.objects.select_related('client', 'executor__user', 'service', 'status'), pk=pk
    )
    related_orders: DjangoQuerySet[Order] = Order.objects.filter(client=order.client) \
                                  .exclude(status__status_name='cancelled') \
                                  .exclude(pk=order.pk) \
                                  .select_related('service', 'status') \
                                  .order_by('-created_at')[:5]
    context: Dict[str, Any] = {
        'order': order,
        'related_orders': related_orders,
    }
    return render(request, 'app_studio/order_detail.html', context)


def user_detail_placeholder(request: HttpRequest, pk: int) -> HttpResponse:
    """Заглушка для детальной страницы пользователя (используется в get_absolute_url)."""
    user: CustomUser = get_object_or_404(CustomUser, pk=pk)
    return HttpResponse(f"Профиль пользователя (заглушка): {user.username} (PK={pk})")

def executor_detail_placeholder(request: HttpRequest, pk: int) -> HttpResponse:
    """Заглушка для детальной страницы исполнителя."""
    executor: Executor = get_object_or_404(Executor.objects.select_related('user'), pk=pk)
    return HttpResponse(f"Профиль исполнителя (заглушка): {executor.user.username} (PK={pk})")

def news_detail_placeholder(request: HttpRequest, pk: int) -> HttpResponse:
    """Заглушка для детальной страницы новости."""
    news_item: News = get_object_or_404(News.objects.select_related('author'), pk=pk)
    return HttpResponse(f"Новость (заглушка): {news_item.title} (PK={pk})")

def cart_detail_placeholder(request: HttpRequest) -> HttpResponse:
    """Заглушка для детальной страницы корзины."""
    if not request.user.is_authenticated:
        return redirect('login') 
    cart, created = Cart.objects.get_or_create(user=request.user)
    return HttpResponse(f"Корзина пользователя (заглушка): {request.user.username} (PK={cart.pk})")

def portfolio_detail_placeholder(request: HttpRequest, pk: int) -> HttpResponse:
    """Заглушка для детальной страницы работы в портфолио."""
    portfolio_item: Portfolio = get_object_or_404(Portfolio.objects.select_related('executor__user'), pk=pk)
    return HttpResponse(f"Работа в портфолио (заглушка): {portfolio_item.title} (PK={pk})")

def service_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Заглушка для детальной страницы услуги."""
    service: Service = get_object_or_404(Service, pk=pk)
    return HttpResponse(f"Детали услуги (заглушка): {service.name} (PK={pk})")