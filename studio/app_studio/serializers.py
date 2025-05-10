from rest_framework import serializers
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
    Сериализатор для смены пароля текущим пользователем.
    """
    old_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password1 = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password2 = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate_old_password(self, value):
        """ Проверяем правильность старого пароля. """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Старый пароль введен неверно.")
        return value

    def validate(self, data):
        """ Проверяем совпадение новых паролей и валидируем новый пароль. """
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({"new_password2": "Новые пароли не совпадают."})

        # Валидируем новый пароль стандартными валидаторами Django
        try:
            validate_password(data['new_password1'], self.context['request'].user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'new_password1': list(e.messages)})

        return data

# --- Базовые сериализаторы для связанных данных ---

class UserSummarySerializer(serializers.ModelSerializer):
    """Краткая информация о пользователе (для отображения в других объектах)."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    avatar_url = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = CustomUser  
        fields = ['pk', 'username', 'full_name', 'avatar_url']

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None

class ExecutorSummarySerializer(serializers.ModelSerializer):
    """Краткая информация об исполнителе."""
    user = UserSummarySerializer(read_only=True)
    class Meta:
        model = Executor
        fields = ['pk', 'user', 'specialization']

class ServiceSummarySerializer(serializers.ModelSerializer):
    """Краткая информация об услуге."""
    photo_url = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Service
        fields = ['pk', 'name', 'price', 'photo_url']
    
    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo and hasattr(obj.photo, 'url') and request:
            try:
                return request.build_absolute_uri(obj.photo.url)
            except Exception:
                return None # На случай ошибки построения URL
        return None

class OrderStatusSerializer(serializers.ModelSerializer):
    """Сериализатор для статуса заказа."""
    display_name = serializers.CharField(source='get_status_name_display', read_only=True)
    class Meta:
        model = OrderStatus
        fields = ['pk', 'status_name', 'display_name']

# --- Основные сериализаторы ---

class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField(read_only=True)

    is_staff = serializers.BooleanField(read_only=True)
    is_executor = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'pk', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'date_joined', 'last_login',
            'avatar', 'avatar_url', 'is_staff', 'is_executor',
        ]
        read_only_fields = ['pk', 'username', 'date_joined', 'last_login', 'avatar_url', 'is_staff', 'is_executor']
        extra_kwargs = {
            'avatar': {'required': False, 'allow_null': True}
        }

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar and hasattr(obj.avatar, 'url') and request:
            try:
                url = obj.avatar.url
                return request.build_absolute_uri(url)
            except Exception as e:
                print(f"Error building avatar URL for user {obj.pk}: {e}")
                return None
        return None
    
    def get_is_executor(self, obj):
        # Проверяем наличие связанного профиля исполнителя
        return hasattr(obj, 'executor_profile') and obj.executor_profile is not None

class ServiceSerializer(serializers.ModelSerializer):
    """Полный сериализатор для Услуги."""
    photo_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Service
        fields = [
            'pk', 'name', 'description', 'price', 'duration_hours',
            'photo', 'photo_url', 'created_at'
        ]
        read_only_fields = ['pk','created_at', 'photo_url']
        extra_kwargs = {
            'photo': {'required': False, 'allow_null': True}
        }

    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo and hasattr(obj.photo, 'url'):
            if request:
                try:
                    absolute_url = request.build_absolute_uri(obj.photo.url)
                    return absolute_url
                except Exception as e:
                    print(f"Error building absolute URL: {e}")
                    return None
            else:
                print("Request not found in context") # Отладка
                try:
                    return obj.photo.url
                except Exception:
                     return None
        else:
             print("No photo or photo.url attribute") # Отладка
        return None

class ExecutorSerializer(serializers.ModelSerializer):
    """portfolio_linkПолный сериализатор для Исполнителя."""
    user = UserSummarySerializer(read_only=True)
    # Показываем полные данные об услугах, которые он предоставляет
    services = ServiceSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Executor
        fields = [
            'pk', 'user', 'specialization', 'experience_years',
            'portfolio_link', 'created_at', 'services'
        ]
        read_only_fields = ['created_at', 'user', 'services']

# --- Сериализаторы для Заказов ---

class OrderReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения (GET) заказов."""
    client = UserSummarySerializer(read_only=True)
    executor = ExecutorSummarySerializer(read_only=True)
    service = ServiceSummarySerializer(read_only=True)
    status = OrderStatusSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'pk', 'client', 'executor', 'service', 'status',
            'created_at', 'scheduled_at', 'completed_at'
        ]
        read_only_fields = fields

class OrderWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления (POST/PUT/PATCH) заказов."""
    client = serializers.HiddenField(default=serializers.CurrentUserDefault())
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())
    executor = serializers.PrimaryKeyRelatedField(queryset=Executor.objects.all(), allow_null=True, required=False)
    status = serializers.PrimaryKeyRelatedField(read_only=True) # Статус будет установлен во view/логике
    # Время по умолчанию +1 день
    scheduled_at = serializers.DateTimeField(default=default_scheduled_at, required=False)

    class Meta:
        model = Order
        fields = [
            'client', 'executor', 'service', 'status', 'scheduled_at',
        ]
        read_only_fields = ['status'] # Статус управляется через actions во ViewSet

    def validate(self, data):
        # выбранный исполнитель должен предоставлять выбранную услугу
        executor = data.get('executor')
        service = data.get('service')
        if executor and service and not ExecutorService.objects.filter(executor=executor, service=service).exists():
             raise serializers.ValidationError({
                 "executor": f"Исполнитель '{executor}' не предоставляет услугу '{service}'."
             })

        # запланированная дата должна быть в будущем
        scheduled = data.get('scheduled_at', default_scheduled_at())
        if scheduled <= timezone.now():
             raise serializers.ValidationError({
                 "scheduled_at": "Запланированная дата выполнения должна быть в будущем."
             })

        return data

    def create(self, validated_data):
        try:
            new_status = OrderStatus.objects.get(status_name='new')
        except OrderStatus.DoesNotExist:
            # критическая ошибка конфигурации
            raise serializers.ValidationError("Статус 'new' не найден в системе.")
        validated_data['status'] = new_status
        return super().create(validated_data)

# --- Другие сериализаторы ---

class ReviewSerializer(serializers.ModelSerializer):
     user = serializers.HiddenField(default=serializers.CurrentUserDefault())
     # Исполнителя и Заказ выбираем при создании
     executor = serializers.PrimaryKeyRelatedField(queryset=Executor.objects.all())
     order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all(), required=False, allow_null=True)

     # Поля для чтения 
     user_read = UserSummarySerializer(source='user', read_only=True)
     executor_read = ExecutorSummarySerializer(source='executor', read_only=True)
     order_read = serializers.PrimaryKeyRelatedField(source='order', read_only=True) 

     class Meta:
         model = Review
         fields = [
             'pk', 'user', 'executor', 'order', 'rating', 'comment', 'created_at',
             'user_read', 'executor_read', 'order_read' # Добавляем поля для чтения
         ]
         read_only_fields = ['pk', 'created_at', 'user_read', 'executor_read', 'order_read']
         # Поля 'user', 'executor', 'order' используются для записи (выбора)

     def validate(self, data):
        request = self.context.get('request')
        user = request.user
        executor = data.get('executor')
        order = data.get('order')

        #  Если указан заказ, он должен принадлежать текущему пользователю
        if order and order.client != user:
            raise serializers.ValidationError({"order": "Вы можете оставить отзыв только на свой заказ."})

        #: Если указан заказ, исполнитель в отзыве должен совпадать с исполнителем заказа
        if order and order.executor != executor:
            raise serializers.ValidationError({"executor": "Исполнитель в отзыве не совпадает с исполнителем заказа."})

        # Нельзя оставить отзыв на самого себя
        if executor.user == user:
             raise serializers.ValidationError({"executor": "Нельзя оставить отзыв на самого себя."})

        # Можно ли оставить отзыв без заказа? 
        # Проверяем уникальность 
        if order:
            if Review.objects.filter(user=user, order=order).exists():
                 raise serializers.ValidationError({"order": "Вы уже оставили отзыв на этот заказ."})
       
        return data

class NewsSerializer(serializers.ModelSerializer):
    author = UserSummarySerializer(read_only=True)
    pdf_file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = News
        fields = ['pk', 'title', 'content', 'published_at', 'author', 'pdf_file', 'pdf_file_url']

        read_only_fields = ['pk', 'author', 'pdf_file_url']
        extra_kwargs = {
            'pdf_file': {'required': False, 'allow_null': True},
            'published_at': {'required': False}, 
            'content': {'required': True},
        }
            

    def get_pdf_file_url(self, obj):
        request = self.context.get('request')
        if obj.pdf_file and request:
            return request.build_absolute_uri(obj.pdf_file.url)
        return None

class PortfolioSerializer(serializers.ModelSerializer):
    executor = ExecutorSummarySerializer(read_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Portfolio
        fields = [
            'pk', 'executor', 'title',
            'image', 'image_url', 
            'video_link', 'description', 'uploaded_at'
        ]
        read_only_fields = ['pk', 'executor', 'uploaded_at', 'image_url']
        extra_kwargs = {
            'image': {'required': False, 'allow_null': True},
            'video_link': {'required': False, 'allow_null': True},
            # Описание необязательно
            'description': {'required': False},
        }

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url') and request:
            try:
                url = obj.image.url
                return request.build_absolute_uri(url)
            except Exception as e:
                print(f"Error building image URL for portfolio {obj.pk}: {e}")
                return None
        return None

# --- Сериализаторы для Корзины ---

class CartItemSerializer(serializers.ModelSerializer):
    # Показываем краткую информацию об услуге
    service = ServiceSummarySerializer(read_only=True)
    # Поле для указания ID услуги при добавлении/создании элемента
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(), source='service', write_only=True, required=False
    )
    total_cost = serializers.DecimalField(source='get_cost', max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['pk', 'service', 'service_id', 'quantity', 'added_at', 'total_cost']
        read_only_fields = ['pk', 'added_at', 'service', 'total_cost']
        extra_kwargs = {
            'quantity': {'min_value': 1} # валидация минимального значения
        }

class CartSerializer(serializers.ModelSerializer):
    # Вложенные элементы корзины
    items = CartItemSerializer(many=True, read_only=True)
    total_cost = serializers.DecimalField(source='get_total_cost', max_digits=12, decimal_places=2, read_only=True)
    total_items_count = serializers.IntegerField(source='get_total_items_count', read_only=True)
    total_positions_count = serializers.IntegerField(source='get_total_positions_count', read_only=True)
    # Информация о владельце корзины
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = Cart
        fields = [
            'pk', 'user', 'items', 'created_at', 'updated_at',
            'total_cost', 'total_items_count', 'total_positions_count'
        ]
        read_only_fields = fields # Корзина сама по себе не изменяется через API, только её содержимое

# --- Сериализаторы для Сообщений ---
class MessageSerializer(serializers.ModelSerializer):
    sender = UserSummarySerializer(read_only=True)
    # При создании указываем ID получателя
    receiver = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    # При чтении показываем инфо о получателе
    receiver_read = UserSummarySerializer(source='receiver', read_only=True)

    class Meta:
        model = Message
        fields = [
            'pk', 'sender', 'receiver', 'receiver_read', 'content',
            'sent_at', 'is_read'
        ]
        read_only_fields = ['pk', 'sender', 'sent_at', 'is_read', 'receiver_read']

    def validate_receiver(self, value):
        # Проверяем, не пытается ли пользователь отправить сообщение самому себе
        request = self.context.get('request')
        if request and request.user == value:
            raise serializers.ValidationError("Нельзя отправить сообщение самому себе.")
        return value

    def create(self, validated_data):
        # Автоматически устанавливаем отправителя
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)

# --- Сериализаторы для Промежуточной таблицы ExecutorService ---
class ExecutorServiceSerializer(serializers.ModelSerializer):
    executor = ExecutorSummarySerializer(read_only=True)
    service = ServiceSummarySerializer(read_only=True)
    # Поля для записи
    executor_id = serializers.PrimaryKeyRelatedField(
        queryset=Executor.objects.all(), source='executor', write_only=True
    )
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(), source='service', write_only=True
    )
    effective_price = serializers.DecimalField(source='get_effective_price', max_digits=10, decimal_places=2, read_only=True)


    class Meta:
        model = ExecutorService
        fields = [
            'pk', 'executor', 'service', 'custom_price', 'effective_price',
            'executor_id', 'service_id'
        ]
        read_only_fields = ['pk', 'executor', 'service', 'effective_price']

    def validate(self, data):
        # Проверяет что связь еще не существует 
        executor = data.get('executor')
        service = data.get('service')
        if ExecutorService.objects.filter(executor=executor, service=service).exists():
            raise serializers.ValidationError("Такая связь исполнителя и услуги уже существует.")
        return data

class RegisterSerializer(serializers.ModelSerializer):
    # Добавляем поле для подтверждения пароля, оно не сохраняется в модель
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True, label="Подтвердите пароль")
    #  email обязательный для регистрации
    email = serializers.EmailField(required=True)

    class Meta:
        model = CustomUser
        # Поля, которые принимаем от пользователя при регистрации
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'phone_number']
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}}, # Не возвращаем пароль в ответе
            'first_name': {'required': False},
            'last_name': {'required': False},
            'phone_number': {'required': False},
        }

    def validate_email(self, value):
        """ Проверяем уникальность email (регистронезависимо). """
        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value

    def validate_username(self, value):
         """ Проверяем уникальность username. """
         if CustomUser.objects.filter(username=value).exists():
             raise serializers.ValidationError("Пользователь с таким именем уже существует.")
         return value

    def validate(self, data):
        """
        Общая валидация: совпадение паролей и сложность пароля.
        """
        # Проверяем совпадение паролей
        if data.get('password') != data.get('password2'):
            raise serializers.ValidationError({'password2': "Пароли не совпадают."})

        # Проверяем сложность основного пароля с помощью валидаторов Django
        password = data.get('password')
        if password:
            try:
                validate_password(password)
            except DjangoValidationError as e:
                # Преобразуем ошибки валидации Django в ошибки DRF
                raise serializers.ValidationError({'password': list(e.messages)})

        return data

    def create(self, validated_data):
        """
        Создаем нового пользователя.
        """
        # Удаляем подтверждение пароля, оно не нужно для модели
        validated_data.pop('password2', None)
        # Извлекаем пароль для хеширования
        password = validated_data.pop('password')

        # Создаем пользователя с остальными данными
        user = CustomUser(**validated_data)
        # Устанавливаем хешированный пароль
        user.set_password(password)
        user.save()

        return user