from datetime import timedelta, datetime 
from typing import Optional, Union, TYPE_CHECKING, Any, Tuple, Type, List, Dict 

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse, NoReverseMatch
from django.utils import timezone
from django.db.models import Sum, F, QuerySet as DjangoQuerySet, Manager, Count, ExpressionWrapper, FloatField, DecimalField
from django.db.models.fields.files import ImageFieldFile, FileField 

if TYPE_CHECKING:
    from .models import Service as ServiceModel, Executor as ExecutorModel, Order as OrderModel, Cart as CartModel, CustomUser as CustomUserModel, OrderStatus as OrderStatusModel, CartItem as CartItemModel


def default_scheduled_at() -> datetime:
    """
    Возвращает время, равное текущему времени плюс 1 день.

    Используется для поля scheduled_at в модели Order.

    Returns:
        datetime: Запланированная дата и время.
    """
    return timezone.now() + timedelta(days=1)

class CustomUser(AbstractUser):
    """
    Кастомная модель пользователя, наследующая стандартного AbstractUser.

    Добавляет поля phone_number и avatar.
    """
    phone_number: models.CharField = models.CharField(max_length=20, verbose_name="Телефон", blank=True, null=True)
    avatar: ImageFieldFile = models.ImageField( 
        upload_to='users/avatars/',
        blank=True,
        null=True,
        verbose_name="Аватар"
    )

    class Meta:
        verbose_name: str = "Пользователь"
        verbose_name_plural: str = "Пользователи"
        ordering: List[str] = ['-date_joined']

    def __str__(self) -> str:
        """
        Возвращает строковое представление пользователя.

        Предпочитает полное имя, затем email, затем username.
        """
        display_name: Optional[str] = self.get_full_name()
        if display_name:
            return f"{display_name} ({self.username})"
        return self.email or self.username

    def get_absolute_url(self) -> str:
        """
        Возвращает URL для доступа к объекту пользователя в админ-панели.
        """
        try:
            return reverse('admin:app_studio_customuser_change', args=[self.pk])
        except NoReverseMatch:
             return '#'


class ServiceQuerySet(DjangoQuerySet['ServiceModel']):
    """Кастомный QuerySet для модели Service."""
    def with_zero_orders(self) -> 'ServiceQuerySet':
        """
        Возвращает услуги, у которых нет заказов.

        Returns:
            ServiceQuerySet: QuerySet услуг без заказов.
        """
        return self.annotate(
            order_count=Count('orders')
        ).filter(order_count=0)

    def expensive_services(self, min_price: Union[int, float, DecimalField] = 30000) -> 'ServiceQuerySet':
        """
        Фильтрует услуги с ценой выше или равной min_price.

        Args:
            min_price: Минимальная цена для фильтрации.

        Returns:
            ServiceQuerySet: QuerySet дорогих услуг.
        """
        return self.filter(price__gte=min_price)

    def annotate_duration_info(self) -> 'ServiceQuerySet':
        """
        Аннотирует длительность услуг в днях (предполагая 8-часовой рабочий день).

        Returns:
            ServiceQuerySet: QuerySet услуг с аннотированным полем 'duration_days'.
        """
        return self.annotate(
            duration_days=ExpressionWrapper(
                F('duration_hours') / 8.0,
                output_field=FloatField()
            )
        )

class ServiceManager(Manager['ServiceModel']):
    """Менеджер, использующий ServiceQuerySet."""
    def get_queryset(self) -> ServiceQuerySet:
        """
        Возвращает экземпляр ServiceQuerySet.
        """
        return ServiceQuerySet(self.model, using=self._db)

    def with_zero_orders(self) -> ServiceQuerySet:
        """
        Возвращает услуги, у которых нет заказов, используя ServiceQuerySet.
        """
        return self.get_queryset().with_zero_orders()

    def expensive_services(self, min_price: Union[int, float, DecimalField] = 30000) -> ServiceQuerySet:
        """
        Фильтрует услуги с ценой выше или равной min_price, используя ServiceQuerySet.
        """
        return self.get_queryset().expensive_services(min_price)

    def annotate_duration_info(self) -> ServiceQuerySet:
        """
        Аннотирует длительность услуг в днях, используя ServiceQuerySet.
        """
        return self.get_queryset().annotate_duration_info()


# --- Модели приложения ---
    
class OrderStatus(models.Model):
    """
    Статус заказа (Новый, В обработке и т.д.).
    """
    STATUS_CHOICES: List[Tuple[str, str]] = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменён'),
    ]
    status_name: models.CharField = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        unique=True,
        verbose_name="Системное имя статуса"
    )

    class Meta:
        verbose_name: str = "Статус заказа"
        verbose_name_plural: str = "Статусы заказов"
        ordering: List[str] = ['pk']

    def __str__(self) -> str:
        """
        Возвращает отображаемое имя статуса заказа.
        """
        return self.get_status_name_display()

    def get_absolute_url(self) -> str:
        """
        Возвращает заглушку URL, так как для статусов обычно не нужна отдельная страница.
        """
        return '#'


class Service(models.Model):
    """
    Услуга, предоставляемая студией.
    """
    name: models.CharField = models.CharField(max_length=100, verbose_name="Название услуги")
    description: models.TextField = models.TextField(verbose_name="Описание", blank=True)
    price: models.DecimalField = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Базовая цена")
    duration_hours: models.IntegerField = models.IntegerField(verbose_name="Примерная длительность (часов)")
    photo: ImageFieldFile = models.ImageField(
        upload_to='services/photos/',
        blank=True,
        null=True,
        verbose_name="Фото услуги"
    )
    created_at: models.DateTimeField = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания услуги"
    )
    objects: ServiceManager = ServiceManager()

    class Meta:
        verbose_name: str = "Услуга"
        verbose_name_plural: str = "Услуги"
        ordering: List[str] = ['name']

    def __str__(self) -> str:
        """
        Возвращает название услуги.
        """
        return self.name

    def get_absolute_url(self) -> str:
        """
        Возвращает URL для детального просмотра услуги через API.
        """
        try:
            return reverse('app_studio:service-api-detail', kwargs={'pk': self.pk})
        except NoReverseMatch:
            return '#'


class CostCalculator(models.Model):
    """
    Калькулятор стоимости, связанный с услугой (OneToOne).

    Автоматически рассчитывает `total_cost` на основе `base_price` услуги и `additional_cost`.
    """
    service: models.OneToOneField = models.OneToOneField(
        Service,
        on_delete=models.CASCADE,
        related_name="cost_calculator",
        verbose_name="Услуга"
    )
    base_price: models.DecimalField = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Базовая цена (из услуги)")
    additional_cost: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Дополнительная стоимость (опции)"
    )
    total_cost: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Итоговая стоимость",
        help_text="Рассчитывается автоматически при сохранении."
    )
    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления расчёта"
    )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Переопределенный метод сохранения.

        Устанавливает `base_price` из связанной услуги и рассчитывает `total_cost`.
        """
        if self.service_id: 
            self.base_price = self.service.price
        self.total_cost = self.base_price + (self.additional_cost or 0) 
        super().save(*args, **kwargs)

    class Meta:
        verbose_name: str = "Калькулятор стоимости"
        verbose_name_plural: str = "Калькуляторы стоимости"
        ordering: List[str] = ['-updated_at']

    def __str__(self) -> str:
        """
        Возвращает строковое представление калькулятора.
        """
        return f"Калькулятор для '{self.service.name}'"

    def get_absolute_url(self) -> str:
        """
        Возвращает URL связанной услуги.
        """
        if self.service_id:
            return self.service.get_absolute_url()
        return '#'


class Executor(models.Model):
    """
    Профиль исполнителя (связан с CustomUser через OneToOne).
    """
    user: models.OneToOneField = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="executor_profile",
        verbose_name="Пользователь"
    )
    specialization: models.CharField = models.CharField(max_length=100, verbose_name="Специализация", blank=True)
    experience_years: models.PositiveIntegerField = models.PositiveIntegerField(default=0, verbose_name="Опыт (лет)")
    portfolio_link: models.URLField = models.URLField(blank=True, null=True, verbose_name="Ссылка на внешнее портфолио")
    created_at: models.DateTimeField = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания профиля"
    )
    services: models.ManyToManyField = models.ManyToManyField(
        Service,
        through='ExecutorService',
        related_name='executors',
        verbose_name="Предоставляемые услуги",
        blank=True
    )

    class Meta:
        verbose_name: str = "Исполнитель"
        verbose_name_plural: str = "Исполнители"
        ordering: List[str] = ['user__username']

    def __str__(self) -> str:
        """
        Возвращает имя пользователя исполнителя и его специализацию, если указана.
        """
        spec: str = f" – {self.specialization}" if self.specialization else ""
        return f"{self.user.username}{spec}"

    def get_absolute_url(self) -> str:
        """
        Возвращает URL для детального просмотра профиля исполнителя через API.
        """
        try:
            return reverse('app_studio:executor-api-detail', kwargs={'pk': self.pk})
        except NoReverseMatch:
            return '#'


class Order(models.Model):
    """
    Заказ клиента на услугу.
    """
    client: models.ForeignKey = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders_as_client",
        verbose_name="Клиент"
    )
    executor: models.ForeignKey = models.ForeignKey(
        Executor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders_as_executor",
        verbose_name="Исполнитель"
    )
    service: models.ForeignKey = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders",
        verbose_name="Услуга"
    )
    status: models.ForeignKey = models.ForeignKey(
        OrderStatus,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Статус заказа"
    )
    created_at: models.DateTimeField = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания заказа"
    )
    scheduled_at: models.DateTimeField = models.DateTimeField(
        default=default_scheduled_at,
        verbose_name="Запланированное время выполнения"
    )
    completed_at: Optional[models.DateTimeField] = models.DateTimeField( 
        null=True,
        blank=True,
        verbose_name="Дата фактического завершения заказа"
    )

    class Meta:
        verbose_name: str = "Заказ"
        verbose_name_plural: str = "Заказы"
        ordering: List[str] = ['-created_at']

    def __str__(self) -> str:
        """
        Возвращает информацию о заказе, включая его ID, услугу и клиента.
        """
        client_name: str = self.client.username if self.client_id else "Клиент удален" 
        service_name: str = self.service.name if self.service_id else "Услуга удалена"
        return f"Заказ #{self.pk} ({service_name}) от {client_name}"

    def get_absolute_url(self) -> str:
        """
        Возвращает URL для детального просмотра заказа через API.
        """
        try:
            return reverse('app_studio:order-api-detail', kwargs={'pk': self.pk})
        except NoReverseMatch:
            return '#'


class Review(models.Model):
    """
    Отзыв пользователя об исполнителе.
    Может быть связан с конкретным заказом.
    """
    user: models.ForeignKey = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="reviews_given",
        verbose_name="Автор отзыва"
    )
    executor: models.ForeignKey = models.ForeignKey(
        Executor,
        on_delete=models.CASCADE,
        related_name="reviews_received",
        verbose_name="Исполнитель (объект отзыва)"
    )
    order: Optional[models.ForeignKey] = models.ForeignKey( # Optional
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews',
        verbose_name="Связанный заказ (опционально)"
    )
    rating: models.PositiveSmallIntegerField = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        verbose_name="Оценка"
    )
    comment: models.TextField = models.TextField(verbose_name="Текст комментария", blank=True)
    created_at: models.DateTimeField = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания отзыва"
    )

    class Meta:
        verbose_name: str = "Отзыв"
        verbose_name_plural: str = "Отзывы"
        ordering: List[str] = ['-created_at']

    def __str__(self) -> str:
        """
        Возвращает информацию об отзыве: автор, исполнитель, заказ (если есть), оценка.
        """
        executor_name: str = self.executor.user.username if self.executor_id and self.executor.user_id else "Исполнитель удален"
        user_name: str = self.user.username if self.user_id else "Автор удален"
        order_info: str = f" (Заказ #{self.order.pk})" if self.order_id else ""
        return f"Отзыв от {user_name} на {executor_name}{order_info} ({self.rating}★)"

    def get_absolute_url(self) -> str:
        """
        Возвращает URL профиля исполнителя, к которому оставлен отзыв.
        """
        if self.executor_id:
            return self.executor.get_absolute_url()
        return '#'


class News(models.Model):
    """
    Новость или статья блога.
    Может содержать прикрепленный PDF файл.
    """
    title: models.CharField = models.CharField(max_length=200, verbose_name="Заголовок")
    content: models.TextField = models.TextField(verbose_name="Содержимое")
    published_at: models.DateTimeField = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата публикации"
    )
    author: Optional[models.ForeignKey] = models.ForeignKey( 
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="news_authored",
        verbose_name="Автор"
    )
    pdf_file: FileField = models.FileField( 
        upload_to='news/pdfs/',
        blank=True,
        null=True,
        verbose_name="Прикрепленный PDF файл"
    )

    class Meta:
        verbose_name: str = "Новость"
        verbose_name_plural: str = "Новости"
        ordering: List[str] = ['-published_at']

    def __str__(self) -> str:
        """
        Возвращает заголовок новости.
        """
        return self.title

    def get_absolute_url(self) -> str:
        """
        Возвращает URL для детального просмотра новости через API.
        """
        try:
            return reverse('app_studio:news-api-detail', kwargs={'pk': self.pk})
        except NoReverseMatch:
            return '#'


class Message(models.Model):
    """
    Сообщение между пользователями (внутренняя почта/чат).
    """
    sender: Optional[models.ForeignKey] = models.ForeignKey( 
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_messages",
        verbose_name="Отправитель"
    )
    receiver: Optional[models.ForeignKey] = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="received_messages",
        verbose_name="Получатель"
    )
    content: models.TextField = models.TextField(verbose_name="Текст сообщения")
    sent_at: models.DateTimeField = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата отправки"
    )
    is_read: models.BooleanField = models.BooleanField(default=False, db_index=True, verbose_name="Прочитано")

    class Meta:
        verbose_name: str = "Сообщение"
        verbose_name_plural: str = "Сообщения"
        ordering: List[str] = ['-sent_at']

    def __str__(self) -> str:
        """
        Возвращает информацию о сообщении: отправитель, получатель, статус прочтения, дата.
        """
        sender_name: str = self.sender.username if self.sender_id else "N/A"
        receiver_name: str = self.receiver.username if self.receiver_id else "N/A"
        read_status: str = "✓" if self.is_read else "●"
        return f"{read_status} От {sender_name} к {receiver_name} ({self.sent_at.strftime('%d.%m %H:%M')})"

    def get_absolute_url(self) -> str:
        """
        Возвращает заглушку URL, так как для сообщений обычно не нужна отдельная каноническая страница.
        """
        return '#'


class Cart(models.Model):
    """
    Корзина пользователя (одна на пользователя).

    Содержит методы для расчета общей стоимости и количества товаров.
    """
    user: models.OneToOneField = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="cart",
        verbose_name="Пользователь"
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True, verbose_name="Дата последнего обновления")

    class Meta:
        verbose_name: str = "Корзина пользователя"
        verbose_name_plural: str = "Корзины пользователей"
        ordering: List[str] = ['-updated_at']

    def __str__(self) -> str:
        """
        Возвращает информацию о владельце корзины.
        """
        return f"Корзина пользователя {self.user.username}"

    def get_total_cost(self) -> Union[DecimalField, int]:
        """
        Рассчитывает общую стоимость всех товаров в корзине.

        Returns:
            Union[DecimalField, int]: Общая стоимость или 0.
        """
        if not hasattr(self, 'items') or self.items is None:
            return 0
            
        aggregation: Optional[Dict[str, Any]] = self.items.aggregate(
            total=Sum(F('quantity') * F('service__price'), output_field=models.DecimalField())
        )
        return aggregation['total'] if aggregation and aggregation['total'] is not None else 0


    def get_total_items_count(self) -> int:
        """
        Рассчитывает общее количество единиц товара в корзине.

        Returns:
            int: Общее количество товаров.
        """
        if not hasattr(self, 'items') or self.items is None:
            return 0
            
        aggregation: Optional[Dict[str, Any]] = self.items.aggregate(total_quantity=Sum('quantity'))
        return aggregation['total_quantity'] if aggregation and aggregation['total_quantity'] is not None else 0

    def get_total_positions_count(self) -> int:
        """
        Рассчитывает количество уникальных позиций (услуг) в корзине.

        Returns:
            int: Количество позиций.
        """
        if not hasattr(self, 'items') or self.items is None:
            return 0
        return self.items.count()

    def get_absolute_url(self) -> str:
        """
        Возвращает URL для доступа к корзине через API.
        """
        try:
            return reverse('app_studio:cart-api-detail')
        except NoReverseMatch:
            return '#'

class CartItem(models.Model):
    """
    Элемент (услуга) в корзине пользователя.
    """
    cart: models.ForeignKey = models.ForeignKey(
        Cart,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name="Корзина"
    )
    service: models.ForeignKey = models.ForeignKey(
        Service,
        related_name='cart_items',
        on_delete=models.CASCADE,
        verbose_name="Услуга"
    )
    quantity: models.PositiveIntegerField = models.PositiveIntegerField(default=1, verbose_name="Количество")
    added_at: models.DateTimeField = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name: str = "Элемент корзины"
        verbose_name_plural: str = "Элементы корзины"
        ordering: List[str] = ['-added_at']
        unique_together: Tuple[Tuple[str, str]] = (('cart', 'service'),)

    def __str__(self) -> str:
        """
        Возвращает информацию об элементе корзины: количество и название услуги.
        """
        service_name: str = self.service.name if self.service_id else "Услуга удалена"
        return f"{self.quantity} x {service_name}"

    def get_cost(self) -> Union[DecimalField, int]:
        """
        Рассчитывает стоимость данной позиции (количество * цена услуги).

        Returns:
            Union[DecimalField, int]: Стоимость позиции или 0.
        """
        if self.service_id:
            return self.service.price * self.quantity
        return 0


class Portfolio(models.Model):
    """
    Работа в портфолио исполнителя.
    """
    executor: models.ForeignKey = models.ForeignKey(
        Executor,
        on_delete=models.CASCADE,
        related_name="portfolios",
        verbose_name="Исполнитель"
    )
    title: models.CharField = models.CharField(max_length=150, default="Работа в портфолио", verbose_name="Название работы")
    image: ImageFieldFile = models.ImageField(
        upload_to='portfolio/images/',
        blank=True,
        null=True,
        verbose_name="Изображение работы"
    )
    video_link: Optional[models.URLField] = models.URLField(verbose_name="Ссылка на видео/проект", blank=True, null=True) # Optional
    description: models.TextField = models.TextField(blank=True, verbose_name="Описание работы")
    uploaded_at: models.DateTimeField = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата добавления"
    )

    class Meta:
        verbose_name: str = "Работа в портфолио"
        verbose_name_plural: str = "Портфолио"
        ordering: List[str] = ['-uploaded_at']

    def __str__(self) -> str:
        """
        Возвращает информацию о работе в портфолио: ID, название, исполнитель.
        """
        executor_name: str = self.executor.user.username if self.executor_id and self.executor.user_id else "N/A"
        return f"Портфолио #{self.pk}: {self.title} ({executor_name})"

    def get_absolute_url(self) -> str:
        """
        Возвращает URL для детального просмотра работы в портфолио через API.
        """
        try:
            return reverse('app_studio:portfolio-api-detail', kwargs={'pk': self.pk})
        except NoReverseMatch:
             return '#'


class ExecutorService(models.Model):
    """
    Промежуточная таблица для связи ManyToMany между Executor и Service.

    Позволяет хранить дополнительные атрибуты связи, такие как индивидуальная цена
    услуги для конкретного исполнителя.
    """
    executor: models.ForeignKey = models.ForeignKey(
        Executor,
        on_delete=models.CASCADE,
        verbose_name="Исполнитель"
    )
    service: models.ForeignKey = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        verbose_name="Услуга"
    )
    custom_price: Optional[models.DecimalField] = models.DecimalField( 
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Индивидуальная цена",
        help_text="Укажите, если цена для этого исполнителя отличается от базовой цены услуги."
    )

    class Meta:
        verbose_name: str = "Услуга исполнителя"
        verbose_name_plural: str = "Услуги исполнителей"
        unique_together: Tuple[Tuple[str, str]] = (('executor', 'service'),)
        ordering: List[str] = ['executor__user__username', 'service__name']

    def __str__(self) -> str:
        """
        Возвращает информацию о связи исполнителя и услуги, включая тип цены.
        """
        executor_name: str = self.executor.user.username if self.executor_id and self.executor.user_id else "?"
        service_name: str = self.service.name if self.service_id else "?"
        price_info: str = f" (Инд. цена: {self.custom_price} руб.)" if self.custom_price is not None else " (Базовая цена)"
        return f"{executor_name} -> {service_name}{price_info}"

    def get_effective_price(self) -> Optional[Union[DecimalField, int]]:
        """
        Возвращает актуальную цену услуги для данного исполнителя.

        Если установлена `custom_price`, возвращает её.
        В противном случае, возвращает базовую цену услуги (`service.price`).

        Returns:
            Optional[Union[DecimalField, int]]: Эффективная цена или None, если услуга не определена.
        """
        if self.custom_price is not None:
            return self.custom_price
        elif self.service_id:
             return self.service.price
        return None

    def get_absolute_url(self) -> str:
        """
        Возвращает URL профиля исполнителя, связанного с этой услугой.
        """
        if self.executor_id:
            return self.executor.get_absolute_url()
        return '#'