from typing import Dict, Any, Optional, List, Union, Type
from decimal import Decimal

from rest_framework import serializers
from rest_framework.request import Request
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import (
    Service, CostCalculator, Executor, CustomUser, Order,
    OrderStatus, Review, News, Message, Cart, CartItem, Portfolio,
    ExecutorService, default_scheduled_at
)

class PasswordChangeSerializer(serializers.Serializer):
    """
    Сериализатор для смены пароля текущим аутентифицированным пользователем.
    """
    old_password: serializers.CharField = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password1: serializers.CharField = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password2: serializers.CharField = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate_old_password(self, value: str) -> str:
        """
        Проверяет правильность старого пароля.

        Args:
            value: Введенный старый пароль.

        Returns:
            str: Старый пароль, если он верен.

        Raises:
            serializers.ValidationError: Если старый пароль неверен.
        """
        user: CustomUser = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Старый пароль введен неверно.")
        return value

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Проверяет совпадение новых паролей и валидирует новый пароль согласно правилам Django.

        Args:
            data: Словарь с данными формы ('old_password', 'new_password1', 'new_password2').

        Returns:
            Dict[str, Any]: Валидированные данные.

        Raises:
            serializers.ValidationError: Если новые пароли не совпадают или новый пароль не прошел валидацию.
        """
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({"new_password2": "Новые пароли не совпадают."})

        user: CustomUser = self.context['request'].user
        try:
            validate_password(data['new_password1'], user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'new_password1': list(e.messages)})

        return data

class UserSummarySerializer(serializers.ModelSerializer):
    """
    Сериализатор для краткой информации о пользователе.
    Используется для отображения пользователя в других связанных объектах.
    """
    full_name: serializers.CharField = serializers.CharField(source='get_full_name', read_only=True)
    avatar_url: serializers.SerializerMethodField = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model: Type[CustomUser] = CustomUser
        fields: List[str] = ['pk', 'username', 'full_name', 'avatar_url']

    def get_avatar_url(self, obj: CustomUser) -> Optional[str]:
        """
        Возвращает абсолютный URL аватара пользователя.

        Args:
            obj: Экземпляр модели CustomUser.

        Returns:
            Optional[str]: URL аватара или None, если аватар отсутствует или нет request в контексте.
        """
        request: Optional[Request] = self.context.get('request')
        if obj.avatar and hasattr(obj.avatar, 'url') and request:
            try:
                return request.build_absolute_uri(obj.avatar.url)
            except Exception:
                return None
        return None

class ExecutorSummarySerializer(serializers.ModelSerializer):
    """
    Сериализатор для краткой информации об исполнителе.
    """
    user: UserSummarySerializer = UserSummarySerializer(read_only=True)
    class Meta:
        model: Type[Executor] = Executor
        fields: List[str] = ['pk', 'user', 'specialization']

class ServiceSummarySerializer(serializers.ModelSerializer):
    """
    Сериализатор для краткой информации об услуге.
    """
    photo_url: serializers.SerializerMethodField = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model: Type[Service] = Service
        fields: List[str] = ['pk', 'name', 'price', 'photo_url']

    def get_photo_url(self, obj: Service) -> Optional[str]:
        """
        Возвращает абсолютный URL фотографии услуги.

        Args:
            obj: Экземпляр модели Service.

        Returns:
            Optional[str]: URL фотографии или None.
        """
        request: Optional[Request] = self.context.get('request')
        if obj.photo and hasattr(obj.photo, 'url') and request:
            try:
                return request.build_absolute_uri(obj.photo.url)
            except Exception:
                return None
        return None

class OrderStatusSerializer(serializers.ModelSerializer):
    """
    Сериализатор для статуса заказа.
    Включает отображаемое имя статуса.
    """
    display_name: serializers.CharField = serializers.CharField(source='get_status_name_display', read_only=True)
    class Meta:
        model: Type[OrderStatus] = OrderStatus
        fields: List[str] = ['pk', 'status_name', 'display_name']

class UserSerializer(serializers.ModelSerializer):
    """
    Полный сериализатор для модели CustomUser.
    Включает URL аватара и флаг, является ли пользователь исполнителем.
    """
    avatar_url: serializers.SerializerMethodField = serializers.SerializerMethodField(read_only=True)
    is_staff: serializers.BooleanField = serializers.BooleanField(read_only=True)
    is_executor: serializers.SerializerMethodField = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model: Type[CustomUser] = CustomUser
        fields: List[str] = [
            'pk', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'date_joined', 'last_login',
            'avatar', 'avatar_url', 'is_staff', 'is_executor',
        ]
        read_only_fields: List[str] = ['pk', 'username', 'date_joined', 'last_login', 'avatar_url', 'is_staff', 'is_executor']
        extra_kwargs: Dict[str, Dict[str, bool]] = {
            'avatar': {'required': False, 'allow_null': True}
        }

    def get_avatar_url(self, obj: CustomUser) -> Optional[str]:
        """
        Возвращает абсолютный URL аватара пользователя.

        Args:
            obj: Экземпляр модели CustomUser.

        Returns:
            Optional[str]: URL аватара или None.
        """
        request: Optional[Request] = self.context.get('request')
        if obj.avatar and hasattr(obj.avatar, 'url') and request:
            try:
                url: str = obj.avatar.url
                return request.build_absolute_uri(url)
            except Exception as e:
                print(f"Error building avatar URL for user {obj.pk}: {e}")
                return None
        return None

    def get_is_executor(self, obj: CustomUser) -> bool:
        """
        Проверяет, имеет ли пользователь связанный профиль исполнителя.

        Args:
            obj: Экземпляр модели CustomUser.

        Returns:
            bool: True, если пользователь является исполнителем, иначе False.
        """
        return hasattr(obj, 'executor_profile') and obj.executor_profile is not None

class ServiceSerializer(serializers.ModelSerializer):
    """
    Полный сериализатор для модели Услуги.
    Включает URL фотографии услуги.
    """
    photo_url: serializers.SerializerMethodField = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model: Type[Service] = Service 
        fields: List[str] = [
            'pk', 'name', 'description', 'price', 'duration_hours',
            'photo', 'photo_url', 'created_at'
        ]
        read_only_fields: List[str] = ['pk','created_at', 'photo_url']
        extra_kwargs: Dict[str, Dict[str, bool]] = {
            'photo': {'required': False, 'allow_null': True}
        }

    def get_photo_url(self, obj: Service) -> Optional[str]:
        """
        Возвращает абсолютный URL фотографии услуги.

        Args:
            obj: Экземпляр модели Service.

        Returns:
            Optional[str]: URL фотографии или None.
        """
        request: Optional[Request] = self.context.get('request')
        if obj.photo and hasattr(obj.photo, 'url'):
            if request:
                try:
                    absolute_url: str = request.build_absolute_uri(obj.photo.url)
                    return absolute_url
                except Exception as e:
                    print(f"Error building absolute URL: {e}")
                    return None
            else:
                print("Request not found in context")
                try:
                    return obj.photo.url
                except Exception:
                     return None
        else:
             print("No photo or photo.url attribute")
        return None

class ExecutorSerializer(serializers.ModelSerializer):
    """
    Полный сериализатор для модели Исполнителя.
    Включает краткую информацию о пользователе и список предоставляемых услуг.
    """
    user: UserSummarySerializer = UserSummarySerializer(read_only=True)
    services: ServiceSummarySerializer = ServiceSummarySerializer(many=True, read_only=True)

    class Meta:
        model: Type[Executor] = Executor
        fields: List[str] = [
            'pk', 'user', 'specialization', 'experience_years',
            'portfolio_link', 'created_at', 'services'
        ]
        read_only_fields: List[str] = ['created_at', 'user', 'services']

class OrderReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения (GET) заказов.
    Включает детальную информацию о клиенте, исполнителе, услуге и статусе.
    """
    client: UserSummarySerializer = UserSummarySerializer(read_only=True)
    executor: ExecutorSummarySerializer = ExecutorSummarySerializer(read_only=True)
    service: ServiceSummarySerializer = ServiceSummarySerializer(read_only=True)
    status: OrderStatusSerializer = OrderStatusSerializer(read_only=True)

    class Meta:
        model: Type[Order] = Order
        fields: List[str] = [
            'pk', 'client', 'executor', 'service', 'status',
            'created_at', 'scheduled_at', 'completed_at'
        ]
        read_only_fields: List[str] = fields

class OrderWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания/обновления (POST/PUT/PATCH) заказов.
    Клиент устанавливается автоматически по текущему пользователю.
    Статус заказа устанавливается по умолчанию на 'new' при создании.
    """
    client: serializers.HiddenField = serializers.HiddenField(default=serializers.CurrentUserDefault())
    service: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())
    executor: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(queryset=Executor.objects.all(), allow_null=True, required=False)
    status: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(read_only=True)
    scheduled_at: serializers.DateTimeField = serializers.DateTimeField(default=default_scheduled_at, required=False)

    class Meta:
        model: Type[Order] = Order
        fields: List[str] = [
            'client', 'executor', 'service', 'status', 'scheduled_at',
        ]
        read_only_fields: List[str] = ['status']

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация данных при создании/обновлении заказа.

        Проверяет:
        - Что выбранный исполнитель предоставляет выбранную услугу.
        - Что запланированная дата выполнения находится в будущем.

        Args:
            data: Словарь с данными для валидации.

        Returns:
            Dict[str, Any]: Валидированные данные.

        Raises:
            serializers.ValidationError: Если данные не прошли валидацию.
        """
        executor: Optional[Executor] = data.get('executor')
        service: Optional[Service] = data.get('service')
        if executor and service and not ExecutorService.objects.filter(executor=executor, service=service).exists():
             raise serializers.ValidationError({
                 "executor": f"Исполнитель '{executor}' не предоставляет услугу '{service}'."
             })

        scheduled: Union[timezone.datetime, Any] = data.get('scheduled_at', default_scheduled_at()) 
        if scheduled <= timezone.now(): 
             raise serializers.ValidationError({
                 "scheduled_at": "Запланированная дата выполнения должна быть в будущем."
             })

        return data

    def create(self, validated_data: Dict[str, Any]) -> Order:
        """
        Создает новый объект Order.
        Устанавливает статус заказа 'new' по умолчанию.

        Args:
            validated_data: Валидированные данные для создания заказа.

        Returns:
            Order: Созданный экземпляр заказа.

        Raises:
            serializers.ValidationError: Если статус 'new' не найден в системе.
        """
        try:
            new_status: OrderStatus = OrderStatus.objects.get(status_name='new')
        except OrderStatus.DoesNotExist:
            raise serializers.ValidationError("Статус 'new' не найден в системе.")
        validated_data['status'] = new_status
        return super().create(validated_data)

class ReviewSerializer(serializers.ModelSerializer):
    """
    Сериализатор для Отзывов.
    Пользователь (автор отзыва) устанавливается автоматически.
    Включает поля для чтения с детальной информацией о пользователе, исполнителе и заказе.
    """
    user: serializers.HiddenField = serializers.HiddenField(default=serializers.CurrentUserDefault())
    executor: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(queryset=Executor.objects.all())
    order: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(queryset=Order.objects.filter(status__status_name='completed'), required=False, allow_null=True)

    user_read: UserSummarySerializer = UserSummarySerializer(source='user', read_only=True)
    executor_read: ExecutorSummarySerializer = ExecutorSummarySerializer(source='executor', read_only=True)
    order_read: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(source='order', read_only=True)

    class Meta:
        model: Type[Review] = Review 
        fields: List[str] = [
            'pk', 'user', 'executor', 'order', 'rating', 'comment', 'created_at',
            'user_read', 'executor_read', 'order_read'
        ]
        read_only_fields: List[str] = ['pk', 'created_at', 'user_read', 'executor_read', 'order_read']

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация данных при создании/обновлении отзыва.

        Проверяет:
        - Если указан заказ, он должен принадлежать текущему пользователю.
        - Если указан заказ, исполнитель в отзыве должен совпадать с исполнителем заказа.
        - Заказ должен быть выполнен.
        - Нельзя оставить отзыв на самого себя.
        - Уникальность отзыва для конкретного заказа от конкретного пользователя.

        Args:
            data: Словарь с данными для валидации.

        Returns:
            Dict[str, Any]: Валидированные данные.

        Raises:
            serializers.ValidationError: Если данные не прошли валидацию.
        """
        request: Request = self.context.get('request') 
        user: CustomUser = request.user 
        executor: Executor = data.get('executor') 
        order: Optional[Order] = data.get('order') 

        if order:
            if order.client != user:
                raise serializers.ValidationError({"order": "Вы можете оставить отзыв только на свой заказ."})
            if order.executor != executor:
                raise serializers.ValidationError({"executor": "Исполнитель в отзыве не совпадает с исполнителем заказа."})
            if order.status and order.status.status_name != 'completed': 
                raise serializers.ValidationError({"order": "Отзыв можно оставить только на выполненный заказ."})
            if Review.objects.filter(user=user, order=order).exists():
                 raise serializers.ValidationError({"order": "Вы уже оставили отзыв на этот заказ."})

        if executor.user == user: 
             raise serializers.ValidationError({"executor": "Нельзя оставить отзыв на самого себя."})

        return data

class NewsSerializer(serializers.ModelSerializer):
    """
    Сериализатор для Новостей.
    Включает информацию об авторе и URL для PDF-файла.
    """
    author: UserSummarySerializer = UserSummarySerializer(read_only=True)
    pdf_file_url: serializers.SerializerMethodField = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model: Type[News] = News 
        fields: List[str] = ['pk', 'title', 'content', 'published_at', 'author', 'pdf_file', 'pdf_file_url']
        read_only_fields: List[str] = ['pk', 'author', 'pdf_file_url']
        extra_kwargs: Dict[str, Dict[str, Any]] = {
            'pdf_file': {'required': False, 'allow_null': True},
            'published_at': {'required': False},
            'content': {'required': True},
        }

    def get_pdf_file_url(self, obj: News) -> Optional[str]:
        """
        Возвращает абсолютный URL для прикрепленного PDF-файла новости.

        Args:
            obj: Экземпляр модели News.

        Returns:
            Optional[str]: URL PDF-файла или None.
        """
        request: Optional[Request] = self.context.get('request')
        if obj.pdf_file and hasattr(obj.pdf_file, 'url') and request:
            return request.build_absolute_uri(obj.pdf_file.url)
        return None

class PortfolioSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работ в Портфолио.
    Включает информацию об исполнителе и URL изображения.
    """
    executor: ExecutorSummarySerializer = ExecutorSummarySerializer(read_only=True)
    image_url: serializers.SerializerMethodField = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model: Type[Portfolio] = Portfolio 
        fields: List[str] = [
            'pk', 'executor', 'title',
            'image', 'image_url',
            'video_link', 'description', 'uploaded_at'
        ]
        read_only_fields: List[str] = ['pk', 'executor', 'uploaded_at', 'image_url']
        extra_kwargs: Dict[str, Dict[str, bool]] = {
            'image': {'required': False, 'allow_null': True},
            'video_link': {'required': False, 'allow_null': True},
            'description': {'required': False},
        }

    def get_image_url(self, obj: Portfolio) -> Optional[str]:
        """
        Возвращает абсолютный URL изображения работы из портфолио.

        Args:
            obj: Экземпляр модели Portfolio.

        Returns:
            Optional[str]: URL изображения или None.
        """
        request: Optional[Request] = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url') and request:
            try:
                url: str = obj.image.url
                return request.build_absolute_uri(url)
            except Exception as e:
                print(f"Error building image URL for portfolio {obj.pk}: {e}")
                return None
        return None

class CartItemSerializer(serializers.ModelSerializer):
    """
    Сериализатор для Элементов корзины.
    Показывает краткую информацию об услуге и общую стоимость позиции.
    """
    service: ServiceSummarySerializer = ServiceSummarySerializer(read_only=True)
    service_id: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(), source='service', write_only=True, required=False
    )
    total_cost: serializers.DecimalField = serializers.DecimalField(source='get_cost', max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model: Type[CartItem] = CartItem 
        fields: List[str] = ['pk', 'service', 'service_id', 'quantity', 'added_at', 'total_cost']
        read_only_fields: List[str] = ['pk', 'added_at', 'service', 'total_cost']
        extra_kwargs: Dict[str, Dict[str, Any]] = {
            'quantity': {'min_value': 1}
        }

class CartSerializer(serializers.ModelSerializer):
    """
    Сериализатор для Корзины.
    Включает список элементов корзины, общую стоимость, количество товаров и позиций,
    а также информацию о владельце корзины.
    """
    items: CartItemSerializer = CartItemSerializer(many=True, read_only=True)
    total_cost: serializers.DecimalField = serializers.DecimalField(source='get_total_cost', max_digits=12, decimal_places=2, read_only=True)
    total_items_count: serializers.IntegerField = serializers.IntegerField(source='get_total_items_count', read_only=True)
    total_positions_count: serializers.IntegerField = serializers.IntegerField(source='get_total_positions_count', read_only=True)
    user: UserSummarySerializer = UserSummarySerializer(read_only=True)

    class Meta:
        model: Type[Cart] = Cart 
        fields: List[str] = [
            'pk', 'user', 'items', 'created_at', 'updated_at',
            'total_cost', 'total_items_count', 'total_positions_count'
        ]
        read_only_fields: List[str] = fields

class MessageSerializer(serializers.ModelSerializer):
    """
    Сериализатор для Сообщений.
    Отправитель устанавливается автоматически. Показывает информацию об отправителе и получателе.
    """
    sender: UserSummarySerializer = UserSummarySerializer(read_only=True)
    receiver: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    receiver_read: UserSummarySerializer = UserSummarySerializer(source='receiver', read_only=True)

    class Meta:
        model: Type[Message] = Message 
        fields: List[str] = [
            'pk', 'sender', 'receiver', 'receiver_read', 'content',
            'sent_at', 'is_read'
        ]
        read_only_fields: List[str] = ['pk', 'sender', 'sent_at', 'is_read', 'receiver_read']

    def validate_receiver(self, value: CustomUser) -> CustomUser:
        """
        Проверяет, что пользователь не пытается отправить сообщение самому себе.

        Args:
            value: Экземпляр CustomUser (получатель).

        Returns:
            CustomUser: Получатель, если валидация прошла.

        Raises:
            serializers.ValidationError: Если пользователь пытается отправить сообщение себе.
        """
        request: Optional[Request] = self.context.get('request')
        if request and request.user == value:
            raise serializers.ValidationError("Нельзя отправить сообщение самому себе.")
        return value

    def create(self, validated_data: Dict[str, Any]) -> Message:
        """
        Создает новый объект Message.
        Автоматически устанавливает отправителя по текущему пользователю.

        Args:
            validated_data: Валидированные данные для создания сообщения.

        Returns:
            Message: Созданный экземпляр сообщения.
        """
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)

class ExecutorServiceSerializer(serializers.ModelSerializer):
    """
    Сериализатор для связи Исполнитель-Услуга (ExecutorService).
    Показывает информацию об исполнителе, услуге и эффективной цене.
    """
    executor: ExecutorSummarySerializer = ExecutorSummarySerializer(read_only=True)
    service: ServiceSummarySerializer = ServiceSummarySerializer(read_only=True)
    executor_id: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(
        queryset=Executor.objects.all(), source='executor', write_only=True
    )
    service_id: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(), source='service', write_only=True
    )
    effective_price: serializers.DecimalField = serializers.DecimalField(source='get_effective_price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model: Type[ExecutorService] = ExecutorService 
        fields: List[str] = [
            'pk', 'executor', 'service', 'custom_price', 'effective_price',
            'executor_id', 'service_id'
        ]
        read_only_fields: List[str] = ['pk', 'executor', 'service', 'effective_price']

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация данных при создании связи Исполнитель-Услуга.
        Проверяет, что такая связь еще не существует.

        Args:
            data: Словарь с данными для валидации.

        Returns:
            Dict[str, Any]: Валидированные данные.

        Raises:
            serializers.ValidationError: Если связь уже существует.
        """
        executor: Optional[Executor] = data.get('executor')
        service: Optional[Service] = data.get('service')
        if executor and service and ExecutorService.objects.filter(executor=executor, service=service).exists():
            raise serializers.ValidationError("Такая связь исполнителя и услуги уже существует.")
        return data

class RegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации нового пользователя.
    Включает поля для пароля и его подтверждения, а также валидацию email, username и пароля.
    """
    password2: serializers.CharField = serializers.CharField(style={'input_type': 'password'}, write_only=True, label="Подтвердите пароль")
    email: serializers.EmailField = serializers.EmailField(required=True)

    class Meta:
        model: Type[CustomUser] = CustomUser
        fields: List[str] = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'phone_number']
        extra_kwargs: Dict[str, Dict[str, Any]] = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'phone_number': {'required': False},
        }

    def validate_email(self, value: str) -> str:
        """
        Проверяет уникальность email (регистронезависимо).

        Args:
            value: Email для проверки.

        Returns:
            str: Email, если он уникален.

        Raises:
            serializers.ValidationError: Если пользователь с таким email уже существует.
        """
        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value

    def validate_username(self, value: str) -> str:
        """
        Проверяет уникальность username.

        Args:
            value: Username для проверки.

        Returns:
            str: Username, если он уникален.

        Raises:
            serializers.ValidationError: Если пользователь с таким именем уже существует.
        """
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким именем уже существует.")
        return value

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Общая валидация данных регистрации.
        Проверяет совпадение паролей и сложность основного пароля.

        Args:
            data: Словарь с данными формы регистрации.

        Returns:
            Dict[str, Any]: Валидированные данные.

        Raises:
            serializers.ValidationError: Если пароли не совпадают или основной пароль не прошел валидацию.
        """
        if data.get('password') != data.get('password2'):
            raise serializers.ValidationError({'password2': "Пароли не совпадают."})

        password: Optional[str] = data.get('password')
        if password:
            try:
                validate_password(password, user=None) # Передаем user=None, если пользователь еще не создан
            except DjangoValidationError as e:
                raise serializers.ValidationError({'password': list(e.messages)})
        return data

    def create(self, validated_data: Dict[str, Any]) -> CustomUser:
        """
        Создает нового пользователя.
        Удаляет поле 'password2' и хеширует пароль перед сохранением.

        Args:
            validated_data: Валидированные данные для создания пользователя.

        Returns:
            CustomUser: Созданный экземпляр пользователя.
        """
        validated_data.pop('password2', None)
        password: str = validated_data.pop('password')

        user: CustomUser = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user