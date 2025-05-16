from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse, NoReverseMatch
from django.utils import timezone
from django.db.models import Sum, F # для Cart.get_total_cost

def default_scheduled_at():
    """
    Возвращает время, равное текущему времени плюс 1 день.
    Используется для поля scheduled_at в модели Order.
    """
    return timezone.now() + timedelta(days=1)

class CustomUser(AbstractUser):
    """
    Кастомная модель пользователя, наследующая стандартного AbstractUser.
    Добавляет поле phone_number.
    """
    phone_number = models.CharField(max_length=20, verbose_name="Телефон", blank=True, null=True)
    avatar = models.ImageField(
        upload_to='users/avatars/',
        blank=True,
        null=True,
        verbose_name="Аватар"
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['-date_joined']

    def __str__(self):
        display_name = self.get_full_name()
        if display_name:
            return f"{display_name} ({self.username})"
        return self.email or self.username

    def get_absolute_url(self):
        try:
            return reverse('admin:app_studio_customuser_change', args=[self.pk])
        except NoReverseMatch:
             return '#'


# --- Кастомный QuerySet и Менеджер для Service ---
class ServiceQuerySet(models.QuerySet):
    """Кастомный QuerySet для модели Service."""
    def with_zero_orders(self):
        """Возвращает услуги, у которых нет заказов."""
        return self.annotate(
            order_count=models.Count('orders')
        ).filter(order_count=0)

    def expensive_services(self, min_price=30000):
        """Фильтрует услуги с ценой выше или равной min_price."""
        return self.filter(price__gte=min_price)

    def annotate_duration_info(self):
        """Аннотирует длительность услуг в днях (предполагая 8-часовой рабочий день)."""
        return self.annotate(
            duration_days=models.ExpressionWrapper(
                models.F('duration_hours') / 8.0, # 8.0 для float division
                output_field=models.FloatField()
            )
        )

class ServiceManager(models.Manager):
    """Менеджер, использующий ServiceQuerySet."""
    def get_queryset(self):
        return ServiceQuerySet(self.model, using=self._db)

    def with_zero_orders(self):
        return self.get_queryset().with_zero_orders()

    def expensive_services(self, min_price=30000):
        return self.get_queryset().expensive_services(min_price)

    def annotate_duration_info(self):
        return self.get_queryset().annotate_duration_info()


# --- Модели приложения ---

class OrderStatus(models.Model):
    """Статус заказа (Новый, В обработке и т.д.)."""
    STATUS_CHOICES = (
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменён'),
    )
    status_name = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        unique=True,
        verbose_name="Системное имя статуса"
    )

    class Meta:
        verbose_name = "Статус заказа"
        verbose_name_plural = "Статусы заказов"
        ordering = ['pk']

    def __str__(self):
        return self.get_status_name_display()

    def get_absolute_url(self):
         return '#'


class Service(models.Model):
    """Услуга, предоставляемая студией."""
    name = models.CharField(max_length=100, verbose_name="Название услуги")
    description = models.TextField(verbose_name="Описание", blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Базовая цена")
    duration_hours = models.IntegerField(verbose_name="Примерная длительность (часов)")
    photo = models.ImageField(
        upload_to='services/photos/',
        blank=True,
        null=True,
        verbose_name="Фото услуги"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания услуги"
    )
    objects = ServiceManager()

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        try:
            return reverse('app_studio:service-api-detail', kwargs={'pk': self.pk}) # Ссылка на API
        except NoReverseMatch:
            return '#'


class CostCalculator(models.Model):
    """Калькулятор стоимости, связанный с услугой (OneToOne)."""
    service = models.OneToOneField(
        Service,
        on_delete=models.CASCADE,
        related_name="cost_calculator",
        verbose_name="Услуга"
    )
    base_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Базовая цена (из услуги)")
    additional_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Дополнительная стоимость (опции)"
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Итоговая стоимость",
        help_text="Рассчитывается автоматически при сохранении."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления расчёта"
    )

    def save(self, *args, **kwargs):
        if self.service:
            self.base_price = self.service.price
        self.total_cost = self.base_price + self.additional_cost
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Калькулятор стоимости"
        verbose_name_plural = "Калькуляторы стоимости"
        ordering = ['-updated_at']

    def __str__(self):
        return f"Калькулятор для '{self.service.name}'"

    def get_absolute_url(self):
        return self.service.get_absolute_url()


class Executor(models.Model):
    """Профиль исполнителя (связан с CustomUser через OneToOne)."""
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="executor_profile",
        verbose_name="Пользователь"
    )
    specialization = models.CharField(max_length=100, verbose_name="Специализация", blank=True)
    experience_years = models.PositiveIntegerField(default=0, verbose_name="Опыт (лет)")
    portfolio_link = models.URLField(blank=True, null=True, verbose_name="Ссылка на внешнее портфолио")
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания профиля"
    )
    services = models.ManyToManyField(
        Service,
        through='ExecutorService',
        related_name='executors',
        verbose_name="Предоставляемые услуги",
        blank=True
    )

    class Meta:
        verbose_name = "Исполнитель"
        verbose_name_plural = "Исполнители"
        ordering = ['user__username']

    def __str__(self):
        spec = f" – {self.specialization}" if self.specialization else ""
        return f"{self.user.username}{spec}"

    def get_absolute_url(self):
        try:
            return reverse('app_studio:executor-api-detail', kwargs={'pk': self.pk}) # Ссылка на API
        except NoReverseMatch:
            return '#'


class Order(models.Model):
    """Заказ клиента на услугу."""
    client = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders_as_client",
        verbose_name="Клиент"
    )
    executor = models.ForeignKey(
        Executor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders_as_executor",
        verbose_name="Исполнитель"
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders",
        verbose_name="Услуга"
    )
    status = models.ForeignKey(
        OrderStatus,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Статус заказа"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания заказа"
    )
    scheduled_at = models.DateTimeField(
        default=default_scheduled_at,
        verbose_name="Запланированное время выполнения"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата фактического завершения заказа"
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']

    def __str__(self):
        client_name = self.client.username if self.client else "Клиент удален"
        service_name = self.service.name if self.service else "Услуга удалена"
        return f"Заказ #{self.pk} ({service_name}) от {client_name}"

    def get_absolute_url(self):
        try:
            return reverse('app_studio:order-api-detail', kwargs={'pk': self.pk}) # Ссылка на API
        except NoReverseMatch:
            return '#'


class Review(models.Model):
    """Отзыв пользователя об исполнителе."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="reviews_given",
        verbose_name="Автор отзыва"
    )
    executor = models.ForeignKey(
        Executor,
        on_delete=models.CASCADE,
        related_name="reviews_received",
        verbose_name="Исполнитель (объект отзыва)"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews',
        verbose_name="Связанный заказ (опционально)"
        )
    rating = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        verbose_name="Оценка"
    )
    comment = models.TextField(verbose_name="Текст комментария", blank=True)
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания отзыва"
    )

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-created_at']

    def __str__(self):
        executor_name = self.executor.user.username if self.executor and self.executor.user else "Исполнитель удален"
        user_name = self.user.username if self.user else "Автор удален"
        order_info = f" (Заказ #{self.order.pk})" if self.order else ""
        return f"Отзыв от {user_name} на {executor_name}{order_info} ({self.rating}★)"

    def get_absolute_url(self):
        return self.executor.get_absolute_url()


class News(models.Model):
    """Новость или статья блога."""
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержимое")
    published_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата публикации"
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="news_authored",
        verbose_name="Автор"
    )
    pdf_file = models.FileField(
        upload_to='news/pdfs/',
        blank=True,
        null=True,
        verbose_name="Прикрепленный PDF файл"
    )

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        try:
            return reverse('app_studio:news-api-detail', kwargs={'pk': self.pk}) # Ссылка на API
        except NoReverseMatch:
            return '#'


class Message(models.Model):
    """Сообщение между пользователями (внутренняя почта/чат)."""
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_messages",
        verbose_name="Отправитель"
    )
    receiver = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="received_messages",
        verbose_name="Получатель"
    )
    content = models.TextField(verbose_name="Текст сообщения")
    sent_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата отправки"
    )
    is_read = models.BooleanField(default=False, db_index=True, verbose_name="Прочитано")

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ['-sent_at']

    def __str__(self):
        sender_name = self.sender.username if self.sender else "N/A"
        receiver_name = self.receiver.username if self.receiver else "N/A"
        read_status = "✓" if self.is_read else "●"
        return f"{read_status} От {sender_name} к {receiver_name} ({self.sent_at.strftime('%d.%m %H:%M')})"

    def get_absolute_url(self):
        return '#' 


class Cart(models.Model):
    """Корзина пользователя (одна на пользователя)."""
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="cart",
        verbose_name="Пользователь"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата последнего обновления")

    class Meta:
        verbose_name = "Корзина пользователя"
        verbose_name_plural = "Корзины пользователей"
        ordering = ['-updated_at']

    def __str__(self):
        return f"Корзина пользователя {self.user.username}"

    def get_total_cost(self):
        """Рассчитывает общую стоимость всех товаров в корзине."""
        aggregation = self.items.aggregate(
            total=Sum(F('quantity') * F('service__price'), output_field=models.DecimalField())
        )
        return aggregation['total'] or 0

    def get_total_items_count(self):
        """Рассчитывает общее количество единиц товара в корзине."""
        aggregation = self.items.aggregate(total_quantity=Sum('quantity'))
        return aggregation['total_quantity'] or 0

    def get_total_positions_count(self):
        """Рассчитывает количество уникальных позиций (услуг) в корзине."""
        return self.items.count()

    def get_absolute_url(self):
        try:
            # URL для API корзины ( без ID, одна у пользователя)
            return reverse('app_studio:cart-api-detail')
        except NoReverseMatch:
            return '#'

class CartItem(models.Model):
    """Элемент (услуга) в корзине пользователя."""
    cart = models.ForeignKey(
        Cart,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name="Корзина"
        )
    service = models.ForeignKey(
        Service,
        related_name='cart_items',
        on_delete=models.CASCADE,
        verbose_name="Услуга"
        )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name = "Элемент корзины"
        verbose_name_plural = "Элементы корзины"
        ordering = ['-added_at']
        unique_together = (('cart', 'service'),)

    def __str__(self):
        return f"{self.quantity} x {self.service.name}"

    def get_cost(self):
        """Рассчитывает стоимость данной позиции (количество * цена услуги)."""
        if self.service:
            return self.service.price * self.quantity
        return 0


class Portfolio(models.Model):
    """Работа в портфолио исполнителя."""
    executor = models.ForeignKey(
        Executor,
        on_delete=models.CASCADE,
        related_name="portfolios",
        verbose_name="Исполнитель"
    )
    title = models.CharField(max_length=150, default="Работа в портфолио", verbose_name="Название работы")
    image = models.ImageField(
        upload_to='portfolio/images/',
        blank=True,
        null=True,
        verbose_name="Изображение работы"
    )
    video_link = models.URLField(verbose_name="Ссылка на видео/проект", blank=True, null=True)
    description = models.TextField(blank=True, verbose_name="Описание работы")
    uploaded_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата добавления"
    )

    class Meta:
        verbose_name = "Работа в портфолио"
        verbose_name_plural = "Портфолио"
        ordering = ['-uploaded_at']

    def __str__(self):
        executor_name = self.executor.user.username if self.executor and self.executor.user else "N/A"
        return f"Портфолио #{self.pk}: {self.title} ({executor_name})"

    def get_absolute_url(self):
        try:
            return reverse('app_studio:portfolio-api-detail', kwargs={'pk': self.pk}) # Ссылка на API
        except NoReverseMatch:
             return '#'


class ExecutorService(models.Model):
    """
    Промежуточная таблица для связи ManyToMany между Executor и Service.
    Позволяет хранить дополнительные атрибуты связи (например, цену).
    """
    executor = models.ForeignKey(
        Executor,
        on_delete=models.CASCADE,
        verbose_name="Исполнитель"
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        verbose_name="Услуга"
    )
    custom_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Индивидуальная цена",
        help_text="Укажите, если цена для этого исполнителя отличается от базовой цены услуги."
    )

    class Meta:
        verbose_name = "Услуга исполнителя"
        verbose_name_plural = "Услуги исполнителей"
        unique_together = (('executor', 'service'),)
        ordering = ['executor__user__username', 'service__name']

    def __str__(self):
        executor_name = self.executor.user.username if self.executor and self.executor.user else "?"
        service_name = self.service.name if self.service else "?"
        price_info = f" (Инд. цена: {self.custom_price} руб.)" if self.custom_price is not None else " (Базовая цена)"
        return f"{executor_name} -> {service_name}{price_info}"

    def get_effective_price(self):
        """Возвращает актуальную цену (кастомную или базовую)."""
        if self.custom_price is not None:
            return self.custom_price
        elif self.service:
             return self.service.price
        return None 

    def get_absolute_url(self):
        return self.executor.get_absolute_url()