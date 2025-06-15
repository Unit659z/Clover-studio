from decimal import Decimal
import io
import time
from typing import Any, List, Tuple, Optional, Dict, Type, Union

from django.contrib import admin, messages
from django.contrib.admin.options import ModelAdmin 
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count, Sum, Q, F, QuerySet as DjangoQuerySet 
from django.db.models.fields.files import ImageFieldFile 
from django.utils import timezone
from django.utils.html import format_html, mark_safe
from django.http import HttpResponse, HttpRequest 
from django.urls import reverse, NoReverseMatch
from django.core.files.base import ContentFile
from django.forms import ModelForm 

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportlabImage 
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER

from .models import (
    CustomUser, Executor, OrderStatus, Order, Review, News, Message,
    Service, CostCalculator, Cart, CartItem, Portfolio, ExecutorService
)


try:
    font_path: str = 'app_studio/fonts/DejaVuSans.ttf'
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
    print(f"Font DejaVuSans registered successfully from {font_path}")
except Exception as e:
    print(f"ERROR registering font 'DejaVuSans' from {font_path}: {e}. PDF generation might use default fonts.")

def image_thumbnail(image_field: Optional[ImageFieldFile], width: int = 100) -> str:
    """
    Генерирует HTML для миниатюры ImageField.

    Args:
        image_field: Объект ImageFieldFile или None.
        width: Ширина миниатюры в пикселях.

    Returns:
        str: HTML-строка с тегом <img> или "Нет фото".
    """
    if image_field and hasattr(image_field, 'url') and image_field.url:
        return format_html('<img src="{}" width="{}" style="max-height: 100px; object-fit: contain;" />',
                           image_field.url, width)
    return "Нет фото"

class OrderStatusFilter(admin.SimpleListFilter):
    """
    Кастомный фильтр для админ-панели Django по статусу заказа.
    Позволяет фильтровать заказы по их статусам.
    """
    title: str = 'Статус заказа'
    parameter_name: str = 'status_filter'

    def lookups(self, request: HttpRequest, model_admin: ModelAdmin) -> List[Tuple[Any, str]]:
        """
        Возвращает список кортежей (значение_параметра, отображаемое_имя) для отображения в фильтре.
        """
        statuses: DjangoQuerySet[OrderStatus] = OrderStatus.objects.all().order_by('pk')
        return [(status.pk, status.get_status_name_display()) for status in statuses]

    def queryset(self, request: HttpRequest, queryset: DjangoQuerySet[Any]) -> DjangoQuerySet[Any]:
        """
        Фильтрует QuerySet на основе выбранного значения в фильтре.
        """
        if self.value():
            return queryset.filter(status__pk=self.value())
        return queryset

class HasCommentFilter(admin.SimpleListFilter):
    """
    Кастомный фильтр для админ-панели Django по наличию комментария в Отзывах.
    """
    title: str = 'Наличие комментария'
    parameter_name: str = 'has_comment'

    def lookups(self, request: HttpRequest, model_admin: ModelAdmin) -> List[Tuple[str, str]]:
        """
        Возвращает варианты для фильтра: "Есть комментарий" или "Нет комментария".
        """
        return [('yes', 'Есть комментарий'), ('no', 'Нет комментария')]

    def queryset(self, request: HttpRequest, queryset: DjangoQuerySet[Any]) -> DjangoQuerySet[Any]:
        """
        Фильтрует QuerySet на основе наличия или отсутствия текста в поле комментария.
        """
        if self.value() == 'yes':
            return queryset.filter(comment__isnull=False).exclude(comment__exact='')
        if self.value() == 'no':
            return queryset.filter(Q(comment__isnull=True) | Q(comment__exact=''))
        return queryset

class IsAssignedFilter(admin.SimpleListFilter):
    """
    Кастомный фильтр для админ-панели Django, показывающий, назначен ли исполнитель заказу.
    """
    title: str = 'Назначен исполнитель'
    parameter_name: str = 'is_assigned'

    def lookups(self, request: HttpRequest, model_admin: ModelAdmin) -> List[Tuple[str, str]]:
        """
        Возвращает варианты для фильтра: "Да" или "Нет".
        """
        return [('yes', 'Да'), ('no', 'Нет')]

    def queryset(self, request: HttpRequest, queryset: DjangoQuerySet[Any]) -> DjangoQuerySet[Any]:
        """
        Фильтрует QuerySet заказов по наличию или отсутствию назначенного исполнителя.
        """
        if self.value() == 'yes':
            return queryset.filter(executor__isnull=False)
        if self.value() == 'no':
            return queryset.filter(executor__isnull=True)
        return queryset

class ExecutorServiceInline(admin.TabularInline):
    """
    Инлайн-редактор для связи Исполнитель-Услуга в админ-панели.
    Позволяет управлять услугами исполнителя на его странице.
    """
    model: Type[ExecutorService] = ExecutorService
    extra: int = 1
    verbose_name: str = "Навык/Услуга исполнителя"
    verbose_name_plural: str = "Навыки/Услуги исполнителя"
    raw_id_fields: Tuple[str, ...] = ('service',)
    fields: Tuple[str, ...] = ('service', 'custom_price')
    autocomplete_fields: List[str] = ['service']

class PortfolioInline(admin.StackedInline):
    """
    Инлайн-редактор для работ в портфолио исполнителя.
    Позволяет управлять работами портфолио на странице исполнителя.
    """
    model: Type[Portfolio] = Portfolio
    extra: int = 0
    readonly_fields: Tuple[str, ...] = ('uploaded_at',)
    verbose_name: str = "Работа в портфолио"
    verbose_name_plural: str = "Портфолио"
    fieldsets: Tuple[Tuple[Optional[str], Dict[str, Any]], ...] = (
        (None, {
            'fields': ('title', 'video_link', 'description')
        }),
        ('Метаданные', {
            'classes': ('collapse',),
            'fields': ('uploaded_at',),
        }),
    )

class ReviewInline(admin.TabularInline):
    """
    Инлайн для отображения полученных отзывов на странице исполнителя (только для чтения).
    """
    model: Type[Review] = Review
    fk_name: str = "executor"
    extra: int = 0
    readonly_fields: Tuple[str, ...] = ('user_link', 'order_link', 'rating', 'comment_short', 'created_at')
    fields: Tuple[str, ...] = ('user_link', 'order_link', 'rating', 'comment_short', 'created_at')
    verbose_name: str = "Полученный отзыв"
    verbose_name_plural: str = "Полученные отзывы"
    can_delete: bool = False
    ordering: Tuple[str, ...] = ('-created_at',)

    def has_add_permission(self, request: HttpRequest, obj: Optional[Any] = None) -> bool:
        """Запрещает добавление отзывов через этот инлайн."""
        return False

    @admin.display(description='Автор')
    def user_link(self, obj: Review) -> str:
        """Возвращает HTML-ссылку на автора отзыва в админ-панели."""
        if obj.user:
            try:
                link: str = reverse("admin:app_studio_customuser_change", args=[obj.user.pk])
                return format_html('<a href="{}">{}</a>', link, obj.user.username)
            except NoReverseMatch: return obj.user.username
        return "N/A"

    @admin.display(description='Заказ')
    def order_link(self, obj: Review) -> str:
        """Возвращает HTML-ссылку на связанный заказ или текст "Без заказа"."""
        if obj.order:
             try:
                link: str = reverse("admin:app_studio_order_change", args=[obj.order.pk])
                return format_html('<a href="{}">Заказ #{}</a>', link, obj.order.pk)
             except NoReverseMatch: return f"Заказ #{obj.order.pk}"
        return "Без заказа"

    @admin.display(description='Комментарий')
    def comment_short(self, obj: Review) -> str:
        """Возвращает сокращенный текст комментария."""
        return (obj.comment[:50] + '...') if obj.comment and len(obj.comment) > 50 else obj.comment

class OrderInline(admin.TabularInline):
    """
    Инлайн для отображения заказов, связанных с исполнителем (только для чтения).
    """
    model: Type[Order] = Order
    fk_name: str = "executor"
    extra: int = 0
    readonly_fields: Tuple[str, ...] = ('order_link', 'client_link', 'service_link', 'status_colored', 'created_at', 'scheduled_at', 'is_completed')
    fields: Tuple[str, ...] = ('order_link', 'client_link', 'service_link', 'status_colored', 'created_at', 'scheduled_at', 'is_completed')
    verbose_name: str = "Заказ исполнителя"
    verbose_name_plural: str = "Заказы исполнителя"
    can_delete: bool = False
    ordering: Tuple[str, ...] = ('-created_at',)

    def get_queryset(self, request: HttpRequest) -> DjangoQuerySet[Order]:
        """Оптимизирует запрос, выбирая связанные объекты."""
        qs: DjangoQuerySet[Order] = super().get_queryset(request).select_related('client', 'service', 'status')
        return qs

    def has_add_permission(self, request: HttpRequest, obj: Optional[Any] = None) -> bool:
        """Запрещает добавление заказов через этот инлайн."""
        return False

    @admin.display(description='ID Заказа')
    def order_link(self, obj: Order) -> str:
        """Возвращает HTML-ссылку на заказ в админ-панели."""
        try:
            link: str = reverse("admin:app_studio_order_change", args=[obj.pk])
            return format_html('<a href="{}">#{}</a>', link, obj.pk)
        except NoReverseMatch: return f"#{obj.pk}"

    @admin.display(description='Клиент')
    def client_link(self, obj: Order) -> str:
        """Возвращает HTML-ссылку на клиента заказа."""
        if obj.client:
            try:
                link: str = reverse("admin:app_studio_customuser_change", args=[obj.client.pk])
                return format_html('<a href="{}">{}</a>', link, obj.client.username)
            except NoReverseMatch: return obj.client.username
        return "N/A"

    @admin.display(description='Услуга')
    def service_link(self, obj: Order) -> str:
        """Возвращает HTML-ссылку на услугу в заказе."""
        if obj.service:
             try:
                 link: str = reverse("admin:app_studio_service_change", args=[obj.service.pk])
                 return format_html('<a href="{}">{}</a>', link, obj.service.name)
             except NoReverseMatch: return obj.service.name
        return "N/A"

    @admin.display(description='Статус')
    def status_colored(self, obj: Order) -> str:
        """Возвращает HTML-представление статуса заказа с цветовой индикацией."""
        if not obj.status: return "N/A"
        status_name: str = obj.status.status_name
        display_name: str = obj.status.get_status_name_display()
        color: str = {'new': 'blue','processing': 'orange','completed': 'green','cancelled': 'red',}.get(status_name, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, display_name)

    @admin.display(description='Завершен?', boolean=True)
    def is_completed(self, obj: Order) -> bool:
        """Возвращает True, если заказ завершен (имеет дату завершения)."""
        return obj.completed_at is not None

class CostCalculatorInline(admin.StackedInline):
    """
    Инлайн-редактор для Калькулятора стоимости на странице Услуги.
    """
    model: Type[CostCalculator] = CostCalculator
    can_delete: bool = False
    verbose_name_plural: str = 'Параметры стоимости'
    fields: Tuple[str, ...] = ('base_price', 'additional_cost', 'total_cost', 'updated_at')
    readonly_fields: Tuple[str, ...] = ('base_price', 'total_cost', 'updated_at')

class CartItemInline(admin.TabularInline):
    """
    Инлайн для отображения товаров в корзине на странице Корзины пользователя.
    """
    model: Type[CartItem] = CartItem
    extra: int = 0
    readonly_fields: Tuple[str, ...] = ('added_at', 'get_item_cost_display', 'service_link')
    fields: Tuple[str, ...] = ('service_link', 'quantity', 'added_at', 'get_item_cost_display')
    raw_id_fields: Tuple[str, ...] = ('service',)
    autocomplete_fields: List[str] = ['service']
    verbose_name: str = "Товар в корзине"
    verbose_name_plural: str = "Товары в корзине"
    ordering: Tuple[str, ...] = ('-added_at',)

    @admin.display(description='Стоимость позиции')
    def get_item_cost_display(self, obj: CartItem) -> str:
        """Возвращает отформатированную стоимость позиции корзины."""
        return f"{obj.get_cost()} руб."

    @admin.display(description='Услуга')
    def service_link(self, obj: CartItem) -> str:
        """Возвращает HTML-ссылку на услугу в элементе корзины."""
        if obj.service:
            try:
                link: str = reverse("admin:app_studio_service_change", args=[obj.service.pk])
                return format_html('<a href="{}">{}</a>', link, obj.service.name)
            except NoReverseMatch: return obj.service.name
        return "N/A"

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """
    Конфигурация админ-панели для модели CustomUser.
    """
    list_display: Tuple[str, ...] = ('pk', 'username', 'email', 'get_full_name', 'phone_number', 'is_staff', 'is_active', 'date_joined', 'is_executor_display', 'avatar_thumbnail')
    list_display_links: Tuple[str, ...] = ('username', 'email')
    search_fields: Tuple[str, ...] = ('pk', 'username', 'email', 'first_name', 'last_name', 'phone_number')
    list_filter: Tuple[Union[str, Tuple[str, Type[admin.FieldListFilter]]], ...] = ('is_staff', 'is_superuser', 'is_active', 'date_joined', ('executor_profile', admin.EmptyFieldListFilter))
    ordering: Tuple[str, ...] = ('-date_joined',)
    fieldsets: Tuple[Tuple[Optional[str], Dict[str, Any]], ...] = (
        (None, {'fields': ('pk', 'username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'avatar')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'classes': ('collapse',), 'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets: Tuple[Tuple[Optional[str], Dict[str, Any]], ...] = BaseUserAdmin.add_fieldsets + ( 
        ('Контактная информация и Аватар', {'fields': ('phone_number', 'first_name', 'last_name', 'email', 'avatar')}),
    )
    readonly_fields: Tuple[str, ...] = ('pk', 'last_login', 'date_joined', 'avatar_thumbnail')
    list_select_related: Tuple[str, ...] = ('executor_profile',)
    actions: List[str] = [
        'show_active_user_emails_values_list_action',
        'check_if_superuser_exists_action'
    ]

    @admin.display(description='Аватар')
    def avatar_thumbnail(self, obj: CustomUser) -> str:
        """Отображает миниатюру аватара пользователя."""
        return image_thumbnail(obj.avatar, width=40)

    @admin.display(description='Исполнитель?', boolean=True)
    def is_executor_display(self, obj: CustomUser) -> bool:
        """Возвращает True, если пользователь является исполнителем."""
        return hasattr(obj, 'executor_profile') and obj.executor_profile is not None

    @admin.action(description="Email активных выбранных пользователей (values_list)")
    def show_active_user_emails_values_list_action(self, request: HttpRequest, queryset: DjangoQuerySet[CustomUser]) -> None:
        """
        Action: Показывает email активных пользователей из выбранного QuerySet.
        Демонстрирует использование values_list().
        """
        active_users_emails: DjangoQuerySet[Tuple[str]] = queryset.filter(is_active=True).values_list('email', flat=True) 
        active_emails_list: List[str] = [email for email in active_users_emails if email]
        message: str
        if active_emails_list:
            message = "Email выбранных активных пользователей:\n" + "\n".join(active_emails_list)
        else:
            message = "Нет активных пользователей с email среди выбранных."
        self.message_user(request, message, level=messages.INFO) 

    @admin.action(description="Проверить, есть ли суперюзеры в системе (exists)")
    def check_if_superuser_exists_action(self, request: HttpRequest, queryset: DjangoQuerySet[CustomUser]) -> None:
        """
        Action: Проверяет наличие суперпользователей в системе.
        Демонстрирует использование exists().
        """
        message: str
        if CustomUser.objects.filter(is_superuser=True).exists():
            message = "В системе есть как минимум один суперпользователь."
        else:
            message = "В системе нет суперпользователей."
        self.message_user(request, message, level=messages.INFO) 

@admin.register(Executor)
class ExecutorAdmin(admin.ModelAdmin):
    """
    Конфигурация админ-панели для модели Executor.
    """
    list_display: Tuple[str, ...] = ('pk','user_link', 'specialization', 'experience_years', 'portfolio_link_display', 'created_at', 'portfolio_count', 'service_count')
    list_display_links: Tuple[str, ...] = ('pk','user_link',)
    list_filter: Tuple[str, ...] = ('specialization', 'experience_years', 'created_at')
    search_fields: Tuple[str, ...] = ('pk','user__username', 'user__first_name', 'user__last_name', 'specialization', 'pk')
    inlines: List[Union[Type[admin.TabularInline], Type[admin.StackedInline]]] = [ExecutorServiceInline, PortfolioInline, ReviewInline]
    date_hierarchy: str = 'created_at'
    raw_id_fields: Tuple[str, ...] = ('user',)
    autocomplete_fields: List[str] = ['user']
    readonly_fields: Tuple[str, ...] = ('created_at', 'user_link', 'portfolio_count', 'service_count')
    list_select_related: Tuple[str, ...] = ('user',)
    list_prefetch_related: Tuple[str, ...] = ('portfolios', 'services')
    list_per_page: int = 20
    fieldsets: Tuple[Tuple[Optional[str], Dict[str, Any]], ...] = (
        (None, {'fields': ('user_link', 'specialization', 'experience_years', 'portfolio_link')}),
        ('Метаданные', {'classes': ('collapse',), 'fields': ('created_at',)})
    )

    @admin.display(description='Пользователь', ordering='user__username')
    def user_link(self, obj: Executor) -> str:
        """Возвращает HTML-ссылку на связанного пользователя."""
        if obj.user:
            try:
                link: str = reverse("admin:app_studio_customuser_change", args=[obj.user.pk])
                return format_html('<a href="{}">{}</a>', link, obj.user.username)
            except NoReverseMatch: return obj.user.username
        return "N/A"

    @admin.display(description='Портфолио')
    def portfolio_link_display(self, obj: Executor) -> str:
        """Возвращает HTML-ссылку на внешнее портфолио, если указано."""
        if obj.portfolio_link:
            return format_html('<a href="{0}" target="_blank" title="{0}">Ссылка</a>', obj.portfolio_link)
        return "Нет ссылки"

    @admin.display(description='Работ в портфолио')
    def portfolio_count(self, obj: Executor) -> int:
        """Возвращает количество работ в портфолио исполнителя."""
        return obj.portfolios.count()

    @admin.display(description='Услуг')
    def service_count(self, obj: Executor) -> int:
        """Возвращает количество услуг, предоставляемых исполнителем."""
        return obj.services.count() # type: ignore


@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    """
    Конфигурация админ-панели для модели OrderStatus.
    """
    list_display: Tuple[str, ...] = ('pk', 'status_name', 'get_display_name_admin', 'order_count')
    search_fields: Tuple[str, ...] = ('status_name',)
    readonly_fields: Tuple[str, ...] = ('pk', 'order_count')
    fields: Tuple[str, ...] = ('status_name',)

    @admin.display(description='Отображаемое имя')
    def get_display_name_admin(self, obj: OrderStatus) -> str:
        """Возвращает отображаемое имя статуса."""
        return obj.get_status_name_display()

    def get_queryset(self, request: HttpRequest) -> DjangoQuerySet[OrderStatus]:
        """Аннотирует queryset количеством заказов для каждого статуса."""
        queryset: DjangoQuerySet[OrderStatus] = super().get_queryset(request)
        queryset = queryset.annotate(order_count_annotated=Count('orders'))
        return queryset

    @admin.display(description='Кол-во заказов', ordering='order_count_annotated')
    def order_count(self, obj: OrderStatus) -> int:
        """Возвращает аннотированное количество заказов для статуса."""
        return obj.order_count_annotated 


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Конфигурация админ-панели для модели Order.
    """
    list_display: Tuple[str, ...] = ('pk', 'client_link', 'executor_link', 'service_link', 'status_colored', 'created_at', 'scheduled_at', 'is_completed')
    list_display_links: Tuple[str, ...] = ('pk',)
    list_filter: Tuple[Any, ...] = (OrderStatusFilter, IsAssignedFilter, 'created_at', 'scheduled_at', 'completed_at', ('client', admin.RelatedOnlyFieldListFilter), ('executor', admin.RelatedOnlyFieldListFilter), ('service', admin.RelatedOnlyFieldListFilter))
    search_fields: Tuple[str, ...] = ('client__username', 'executor__user__username', 'service__name', 'pk')
    date_hierarchy: str = 'created_at'
    raw_id_fields: Tuple[str, ...] = ('client', 'executor', 'service', 'status')
    autocomplete_fields: List[str] = ['client', 'executor', 'service', 'status']
    readonly_fields: Tuple[str, ...] = ('created_at', 'pk')
    list_select_related: Tuple[str, ...] = ('client', 'executor__user', 'service', 'status')
    actions: List[str] = ['mark_completed', 'mark_processing', 'generate_order_pdf']
    list_per_page: int = 25
    fieldsets: Tuple[Tuple[Optional[str], Dict[str, Any]], ...] = (
        ('Основная информация', {'fields': ('client', 'service', 'executor', 'status')}),
        ('Даты', {'fields': ('created_at', 'scheduled_at', 'completed_at')}),
    )

    @admin.display(description='Клиент', ordering='client__username')
    def client_link(self, obj: Order) -> str:
        """Возвращает HTML-ссылку на клиента заказа."""
        if obj.client:
            try:
                link: str = reverse("admin:app_studio_customuser_change", args=[obj.client.pk])
                return format_html('<a href="{}">{}</a>', link, obj.client.username)
            except NoReverseMatch: return obj.client.username
        return "Клиент удален"

    @admin.display(description='Исполнитель', ordering='executor__user__username')
    def executor_link(self, obj: Order) -> str:
        """Возвращает HTML-ссылку на исполнителя заказа."""
        if obj.executor and obj.executor.user:
             try:
                link: str = reverse("admin:app_studio_executor_change", args=[obj.executor.pk])
                return format_html('<a href="{}">{}</a>', link, obj.executor.user.username)
             except NoReverseMatch: return obj.executor.user.username
        elif obj.executor:
             return "Профиль исполнителя есть, но пользователь удален?"
        return "Не назначен"

    @admin.display(description='Услуга', ordering='service__name')
    def service_link(self, obj: Order) -> str:
        """Возвращает HTML-ссылку на услугу в заказе."""
        if obj.service:
             try:
                 link: str = reverse("admin:app_studio_service_change", args=[obj.service.pk])
                 return format_html('<a href="{}">{}</a>', link, obj.service.name)
             except NoReverseMatch: return obj.service.name
        return "Услуга удалена"

    @admin.display(description='Статус', ordering='status__status_name')
    def status_colored(self, obj: Order) -> str:
        """Возвращает HTML-представление статуса заказа с цветовой индикацией."""
        if not obj.status: return "N/A"
        status_name: str = obj.status.status_name
        display_name: str = obj.status.get_status_name_display()
        color: str = {'new': 'blue','processing': 'orange','completed': 'green','cancelled': 'red',}.get(status_name, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, display_name)

    @admin.display(description='Завершен?', boolean=True, ordering='completed_at')
    def is_completed(self, obj: Order) -> bool:
        """Возвращает True, если заказ завершен."""
        return obj.completed_at is not None

    @admin.action(description='Отметить как "В обработке"')
    def mark_processing(self, request: HttpRequest, queryset: DjangoQuerySet[Order]) -> None:
        """Action: Устанавливает статус "В обработке" для выбранных заказов."""
        try:
            status_processing: OrderStatus = OrderStatus.objects.get(status_name='processing')
            updated_count: int = queryset.update(status=status_processing, completed_at=None)
            self.message_user(request, f"Статус 'В обработке' установлен для {updated_count} заказов.", messages.SUCCESS)
        except OrderStatus.DoesNotExist:
            self.message_user(request, "Ошибка: Статус 'В обработке' не найден.", level=messages.ERROR)
        except Exception as e:
             self.message_user(request, f"Произошла ошибка: {e}", level=messages.ERROR)

    @admin.action(description='Отметить как "Выполнен"')
    def mark_completed(self, request: HttpRequest, queryset: DjangoQuerySet[Order]) -> None:
        """Action: Устанавливает статус "Выполнен" для выбранных заказов."""
        queryset_to_update: DjangoQuerySet[Order] = queryset.exclude(status__status_name__in=['completed', 'cancelled'])
        try:
            status_completed: OrderStatus = OrderStatus.objects.get(status_name='completed')
            now: timezone.datetime = timezone.now()
            updated_count: int = queryset_to_update.update(status=status_completed, completed_at=now)
            self.message_user(request, f"Статус 'Выполнен' установлен для {updated_count} заказов.", messages.SUCCESS)
        except OrderStatus.DoesNotExist:
            self.message_user(request, "Ошибка: Статус 'Выполнен' не найден.", level=messages.ERROR)
        except Exception as e:
             self.message_user(request, f"Произошла ошибка: {e}", level=messages.ERROR)


    @admin.action(description='Сгенерировать PDF для выбранных заказов')
    def generate_order_pdf(self, request: HttpRequest, queryset: DjangoQuerySet[Order]) -> Union[HttpResponse, None]:
        """Action: Генерирует PDF-отчет для выбранных заказов."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        styles: Dict[str, ParagraphStyle] = getSampleStyleSheet() # type: ignore
        styles['Normal'].fontName = 'DejaVuSans'
        styles['Heading1'].fontName = 'DejaVuSans'
        styles['Heading2'].fontName = 'DejaVuSans'
        story: List[Any] = []
        story.append(Paragraph("Отчет по заказам", styles['h1']))
        story.append(Spacer(1, 1*cm))
        for order_obj in queryset.select_related('client', 'executor__user', 'service', 'status'):
             story.append(Paragraph(f"<u>Заказ #{order_obj.pk}</u>", styles['h2']))
             story.append(Spacer(1, 0.2*cm))
             client_str: str = order_obj.client.get_full_name() or order_obj.client.username if order_obj.client else 'Удален'
             executor_str: str = order_obj.executor.user.get_full_name() or order_obj.executor.user.username if order_obj.executor and order_obj.executor.user else 'Не назначен/Удален'
             service_str: str = order_obj.service.name if order_obj.service else 'Удалена'
             status_str: str = order_obj.status.get_status_name_display() if order_obj.status else 'Неизвестен'
             created_str: str = order_obj.created_at.strftime('%d.%m.%Y %H:%M') if order_obj.created_at else '-'
             scheduled_str: str = order_obj.scheduled_at.strftime('%d.%m.%Y %H:%M') if order_obj.scheduled_at else '-'
             completed_str: str = order_obj.completed_at.strftime('%d.%m.%Y %H:%M') if order_obj.completed_at else '-'
             details: List[str] = [ f"<b>Клиент:</b> {client_str}", f"<b>Исполнитель:</b> {executor_str}", f"<b>Услуга:</b> {service_str}", f"<b>Статус:</b> {status_str}", f"<b>Создан:</b> {created_str}", f"<b>План. время:</b> {scheduled_str}", f"<b>Завершен:</b> {completed_str}",]
             for detail in details: story.append(Paragraph(detail, styles['Normal']))
             story.append(Spacer(1, 0.5*cm))
        try:
            doc.build(story)
        except Exception as e:
            return HttpResponse(f"Ошибка генерации PDF: {e}", status=500)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="orders_report.pdf"'
        return response

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Конфигурация админ-панели для модели Review.
    """
    list_display: Tuple[str, ...] = ('pk', 'user_link', 'executor_link', 'order_link', 'rating_stars', 'comment_short', 'created_at')
    list_display_links: Tuple[str, ...] = ('pk',)
    list_filter: Tuple[Any, ...] = ('rating', 'created_at', HasCommentFilter, ('user', admin.RelatedOnlyFieldListFilter), ('executor', admin.RelatedOnlyFieldListFilter), ('order', admin.RelatedOnlyFieldListFilter))
    search_fields: Tuple[str, ...] = ('user__username', 'executor__user__username', 'comment', 'pk', 'order__pk')
    date_hierarchy: str = 'created_at'
    raw_id_fields: Tuple[str, ...] = ('user', 'executor', 'order')
    autocomplete_fields: List[str] = ['user', 'executor', 'order']
    list_select_related: Tuple[str, ...] = ('user', 'executor__user', 'order')
    list_per_page: int = 25

    fields: Tuple[str, ...] = ('user', 'executor', 'order', 'rating', 'comment', 'created_at')
    readonly_fields: Tuple[str, ...] = ('created_at',)

    def get_form(self, request: HttpRequest, obj: Optional[Review] = None, **kwargs: Any) -> Type[ModelForm]:
        """
        Кастомизирует форму редактирования отзыва.
        Фильтрует поле 'user' так, чтобы можно было выбрать только пользователей без профиля исполнителя.
        """
        form: Type[ModelForm] = super().get_form(request, obj, **kwargs)
        if 'user' in form.base_fields:
            form.base_fields['user'].queryset = CustomUser.objects.filter(
                executor_profile__isnull=True
            ).order_by('username')
        return form

    @admin.display(description='Автор', ordering='user__username')
    def user_link(self, obj: Review) -> str:
        """Возвращает HTML-ссылку на автора отзыва."""
        if obj.user:
            try:
                link: str = reverse("admin:app_studio_customuser_change", args=[obj.user.pk])
                return format_html('<a href="{}">{}</a>', link, obj.user.username)
            except NoReverseMatch: return obj.user.username
        return "N/A"

    @admin.display(description='Исполнитель', ordering='executor__user__username')
    def executor_link(self, obj: Review) -> str:
        """Возвращает HTML-ссылку на исполнителя, о котором оставлен отзыв."""
        if obj.executor and obj.executor.user:
            try:
                link: str = reverse("admin:app_studio_executor_change", args=[obj.executor.pk])
                return format_html('<a href="{}">{}</a>', link, obj.executor.user.username)
            except NoReverseMatch: return obj.executor.user.username
        return "N/A"

    @admin.display(description='Заказ', ordering='order__pk')
    def order_link(self, obj: Review) -> str:
        """Возвращает HTML-ссылку на связанный заказ, если он есть."""
        if obj.order:
             try:
                link: str = reverse("admin:app_studio_order_change", args=[obj.order.pk])
                return format_html('<a href="{}">Заказ #{}</a>', link, obj.order.pk)
             except NoReverseMatch: return f"Заказ #{obj.order.pk}"
        return "Без заказа"

    @admin.display(description='Оценка', ordering='rating')
    def rating_stars(self, obj: Review) -> str:
        """Возвращает HTML-представление рейтинга в виде звезд."""
        if obj and obj.rating is not None:
            try:
                rating_value: int = int(obj.rating)
                if 1 <= rating_value <= 5:
                    stars: str = '★' * rating_value + '☆' * (5 - rating_value)
                    return mark_safe(f'<span style="font-size: 1.2em; color: orange;">{stars}</span>')
                else: return f"Рейт.: {obj.rating}"
            except (ValueError, TypeError): return "?"
        return "---"

    @admin.display(description='Комментарий')
    def comment_short(self, obj: Review) -> str:
        """Возвращает сокращенный текст комментария."""
        return (obj.comment[:50] + '...') if obj.comment and len(obj.comment) > 50 else obj.comment

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    """
    Конфигурация админ-панели для модели News.
    """
    list_display: Tuple[str, ...] = ('pk', 'title', 'author_link', 'published_at', 'pdf_link_display', 'content_preview')
    list_display_links: Tuple[str, ...] = ('pk', 'title')
    list_filter: Tuple[Union[str, Tuple[str, Type[admin.FieldListFilter]]], ...] = ('published_at', ('author', admin.RelatedOnlyFieldListFilter))
    search_fields: Tuple[str, ...] = ('title', 'content', 'author__username', 'pk')
    date_hierarchy: str = 'published_at'
    raw_id_fields: Tuple[str, ...] = ('author',)
    autocomplete_fields: List[str] = ['author']
    readonly_fields: Tuple[str, ...] = ('published_at', 'pk', 'author_link', 'pdf_link_display')
    actions: List[str] = ['generate_news_pdf_action', 'find_news_with_exact_case_word_action']
    list_per_page: int = 20
    list_select_related: Tuple[str, ...] = ('author',)
    fieldsets: Tuple[Tuple[Optional[str], Dict[str, Any]], ...] = (
        (None, {'fields': ('title', 'content')}),
        ('Метаданные', {'fields': ('author', 'pdf_file', 'pdf_link_display', 'published_at')}),
    )

    @admin.display(description='Автор', ordering='author__username')
    def author_link(self, obj: News) -> str:
        """Возвращает HTML-ссылку на автора новости."""
        if obj.author:
            try:
                link: str = reverse("admin:app_studio_customuser_change", args=[obj.author.pk])
                return format_html('<a href="{}">{}</a>', link, obj.author.username)
            except NoReverseMatch: return obj.author.username
        return "Автор не указан/удален"

    @admin.display(description='PDF файл')
    def pdf_link_display(self, obj: News) -> str:
        """Возвращает HTML-ссылку для скачивания/просмотра PDF-файла, если он есть."""
        if obj.pdf_file and hasattr(obj.pdf_file, 'url') and obj.pdf_file.url:
             file_url: str = obj.pdf_file.url
             return format_html('<a href="{}" target="_blank">Скачать/Просмотреть</a>', file_url)
        return "Нет файла"

    @admin.display(description='Начало текста')
    def content_preview(self, obj: News) -> str:
        """Возвращает превью содержимого новости."""
        return (obj.content[:100] + '...') if obj.content and len(obj.content) > 100 else obj.content

    @admin.action(description='Сгенерировать PDF и (если 1) сохранить')
    def generate_news_pdf_action(self, request: HttpRequest, queryset: DjangoQuerySet[News]) -> Union[HttpResponse, None]:
        """Action: Генерирует PDF для выбранных новостей и сохраняет файл, если выбрана одна новость."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        styles: Dict[str, ParagraphStyle] = getSampleStyleSheet() 
        styles['Normal'].fontName = 'DejaVuSans'; styles['Normal'].fontSize = 11; styles['Normal'].leading = 14; styles['Normal'].alignment = TA_JUSTIFY
        styles['Heading1'].fontName = 'DejaVuSans'; styles['Heading1'].fontSize = 16; styles['Heading1'].alignment = TA_CENTER; styles['Heading1'].spaceAfter = 0.5*cm
        styles['Heading2'].fontName = 'DejaVuSans'; styles['Heading2'].fontSize = 14; styles['Heading2'].spaceBefore = 0.5*cm; styles['Heading2'].spaceAfter = 0.3*cm

        story: List[Any] = []
        if queryset.count() == 1:
            news_item_single: News = queryset.first() 
            story.append(Paragraph(f"Новость: {news_item_single.title}", styles['h1']))
        else:
            story.append(Paragraph("Дайджест новостей", styles['h1']))

        for news_item_loop in queryset.select_related('author'):
            author_name: str = news_item_loop.author.username if news_item_loop.author else "Неизвестный автор"
            pub_date: str = news_item_loop.published_at.strftime('%d.%m.%Y') if news_item_loop.published_at else "-"
            story.append(Paragraph(news_item_loop.title, styles['h2']))
            story.append(Paragraph(f"<i>Автор: {author_name}, Опубликовано: {pub_date}</i>", styles['Normal']))
            story.append(Spacer(1, 0.2*cm))
            content_paragraphs: List[str] = news_item_loop.content.split('\n')
            for paragraph_text in content_paragraphs:
                if paragraph_text.strip():
                    story.append(Paragraph(paragraph_text, styles['Normal']))
            story.append(Spacer(1, 0.8*cm))

        try:
            doc.build(story)
        except Exception as e:
            self.message_user(request, f"Ошибка генерации PDF: {e}", level=messages.ERROR)
            return HttpResponse(f"Ошибка генерации PDF: {e}", status=500) 

        pdf_content: bytes = buffer.getvalue()
        buffer.close()

        if queryset.count() == 1:
            news_item_save: News = queryset.first() 
            try:
                timestamp: int = int(time.time())
                filename: str = f"news_{news_item_save.pk}_{timestamp}.pdf"
                pdf_file_obj = ContentFile(pdf_content, name=filename)
                news_item_save.pdf_file = pdf_file_obj 
                news_item_save.save(update_fields=['pdf_file'])
                self.message_user(request, f"PDF для новости '{news_item_save.title}' успешно сгенерирован и сохранен.", level=messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f"PDF сгенерирован, но произошла ошибка при сохранении файла для новости '{news_item_save.title}': {e}", level=messages.WARNING)
        elif queryset.count() > 1:
             self.message_user(request, f"PDF-дайджест для {queryset.count()} новостей сгенерирован (файл не сохранен в базу).", level=messages.INFO)
        else:
             self.message_user(request, "Не выбрано ни одной новости.", level=messages.WARNING)
             return None

        response = HttpResponse(pdf_content, content_type='application/pdf')
        download_filename_str: str = "news_report.pdf" if queryset.count() > 1 else f"news_{queryset.first().pk}.pdf" 
        response['Content-Disposition'] = f'attachment; filename="{download_filename_str}"'
        return response

    @admin.action(description="Найти новости со словом 'Django' (регистрозависимо, __contains)")
    def find_news_with_exact_case_word_action(self, request: HttpRequest, queryset: DjangoQuerySet[News]) -> None:
        """Action: Ищет новости с точным вхождением слова 'Django' в заголовке."""
        news_with_word: DjangoQuerySet[News] = queryset.filter(title__contains='Django')
        if news_with_word.exists():
            titles: List[str] = list(news_with_word.values_list('title', flat=True))
            message: str = "Новости, содержащие 'Django' (с учетом регистра) в заголовке:\n" + "\n".join(titles)
            self.message_user(request, message, level=messages.INFO)
        else:
            self.message_user(request, "Не найдено новостей с точным вхождением 'Django' в заголовке среди выбранных.", level=messages.INFO)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Конфигурация админ-панели для модели Message.
    """
    list_display: Tuple[str, ...] = ('pk', 'sender_link', 'receiver_link', 'content_short', 'sent_at', 'is_read')
    list_display_links: Tuple[str, ...] = ('pk',)
    list_filter: Tuple[Any, ...] = ('sent_at', 'is_read', ('sender', admin.RelatedOnlyFieldListFilter), ('receiver', admin.RelatedOnlyFieldListFilter))
    search_fields: Tuple[str, ...] = ('sender__username', 'receiver__username', 'content', 'pk')
    date_hierarchy: str = 'sent_at'
    raw_id_fields: Tuple[str, ...] = ('sender', 'receiver')
    autocomplete_fields: List[str] = ['sender', 'receiver']
    readonly_fields: Tuple[str, ...] = ('sent_at', 'pk', 'sender_link', 'receiver_link')
    list_select_related: Tuple[str, ...] = ('sender', 'receiver')
    list_per_page: int = 30
    actions: List[str] = ['mark_as_read', 'mark_as_unread']
    fields: Tuple[str, ...] = ('sender_link', 'receiver_link', 'sent_at', 'is_read', 'content')

    @admin.display(description='Отправитель', ordering='sender__username')
    def sender_link(self, obj: Message) -> str:
        """Возвращает HTML-ссылку на отправителя сообщения."""
        if obj.sender:
            try:
                link: str = reverse("admin:app_studio_customuser_change", args=[obj.sender.pk])
                return format_html('<a href="{}">{}</a>', link, obj.sender.username)
            except NoReverseMatch: return obj.sender.username
        return "N/A"

    @admin.display(description='Получатель', ordering='receiver__username')
    def receiver_link(self, obj: Message) -> str:
        """Возвращает HTML-ссылку на получателя сообщения."""
        if obj.receiver:
             try:
                link: str = reverse("admin:app_studio_customuser_change", args=[obj.receiver.pk])
                return format_html('<a href="{}">{}</a>', link, obj.receiver.username)
             except NoReverseMatch: return obj.receiver.username
        return "N/A"

    @admin.display(description='Содержимое')
    def content_short(self, obj: Message) -> str:
        """Возвращает сокращенное содержимое сообщения."""
        return (obj.content[:75] + '...') if obj.content and len(obj.content) > 75 else obj.content

    @admin.action(description='Отметить как прочитанные')
    def mark_as_read(self, request: HttpRequest, queryset: DjangoQuerySet[Message]) -> None:
        """Action: Отмечает выбранные сообщения как прочитанные."""
        updated_count: int = queryset.update(is_read=True)
        self.message_user(request, f"{updated_count} сообщений отмечены как прочитанные.", messages.SUCCESS)

    @admin.action(description='Отметить как непрочитанные')
    def mark_as_unread(self, request: HttpRequest, queryset: DjangoQuerySet[Message]) -> None:
        """Action: Отмечает выбранные сообщения как непрочитанные."""
        updated_count: int = queryset.update(is_read=False)
        self.message_user(request, f"{updated_count} сообщений отмечены как непрочитанные.", messages.SUCCESS)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """
    Конфигурация админ-панели для модели Service.
    """
    list_display: Tuple[str, ...] = ('pk', 'thumbnail', 'name', 'price', 'total_cost_display', 'duration_hours', 'created_at', 'order_count_display', 'executor_count_display')
    list_display_links: Tuple[str, ...] = ('pk', 'name')
    list_filter: Tuple[str, ...] = ('created_at',)
    search_fields: Tuple[str, ...] = ('name', 'description', 'pk')
    date_hierarchy: str = 'created_at'
    readonly_fields: Tuple[str, ...] = ('created_at', 'pk', 'thumbnail', 'order_count_display', 'executor_count_display', 'total_cost_display')
    inlines: List[Union[Type[admin.StackedInline]]] = [CostCalculatorInline]
    actions: List[str] = [
        'show_service_order_count',
        'show_expensive_service_count',
        'show_service_names_prices_values_action'
    ]
    list_per_page: int = 20
    list_select_related: Tuple[str, ...] = ('cost_calculator',)
    fieldsets: Tuple[Tuple[Optional[str], Dict[str, Any]], ...] = (
        (None, {'fields': ('name', 'description', 'price', 'duration_hours')}),
        ('Изображение', {'fields': ('photo', 'thumbnail')}),
        ('Метаданные', {'classes': ('collapse',), 'fields': ('created_at',)}),
    )

    def get_queryset(self, request: HttpRequest) -> DjangoQuerySet[Service]:
        """Аннотирует queryset количеством заказов и исполнителей для каждой услуги."""
        qs: DjangoQuerySet[Service] = super().get_queryset(request).select_related('cost_calculator')
        qs = qs.annotate(
            order_count_annotated=Count('orders', distinct=True),
            executor_count_annotated=Count('executors', distinct=True)
        )
        return qs

    @admin.display(description='Миниатюра')
    def thumbnail(self, obj: Service) -> str:
        """Отображает миниатюру изображения услуги."""
        return image_thumbnail(obj.photo, width=80)

    @admin.display(description='Итоговая цена', ordering='cost_calculator__total_cost')
    def total_cost_display(self, obj: Service) -> str:
        """Отображает итоговую стоимость услуги (с учетом калькулятора) или базовую цену."""
        if hasattr(obj, 'cost_calculator') and obj.cost_calculator:
            return f"{obj.cost_calculator.total_cost} руб."
        elif obj.price is not None:
             return f"{obj.price} руб. (базовая)"
        return "N/A"

    @admin.display(description='Кол-во заказов', ordering='order_count_annotated')
    def order_count_display(self, obj: Service) -> int:
        """Отображает аннотированное количество заказов для услуги."""
        return obj.order_count_annotated 

    @admin.display(description='Кол-во исполнителей', ordering='executor_count_annotated')
    def executor_count_display(self, obj: Service) -> int:
        """Отображает аннотированное количество исполнителей для услуги."""
        return obj.executor_count_annotated 

    @admin.action(description="Показать количество заказов для выбранных услуг")
    def show_service_order_count(self, request: HttpRequest, queryset: DjangoQuerySet[Service]) -> None:
        """Action: Показывает сообщение с количеством заказов для каждой из выбранных услуг."""
        annotated_queryset: DjangoQuerySet[Service] = queryset.annotate(order_count=Count('orders', distinct=True))
        message_lines: List[str] = ["Количество заказов для выбранных услуг:"]
        for service_item in annotated_queryset:
            message_lines.append(f"- {service_item.name}: {service_item.order_count}") 

        message: str = "\n".join(message_lines)
        self.message_user(request, message, level=messages.INFO)

    @admin.action(description="Показать кол-во услуг с ценой >= 30000")
    def show_expensive_service_count(self, request: HttpRequest, queryset: DjangoQuerySet[Service]) -> None:
        """Action: Показывает количество услуг с ценой выше или равной 30000."""
        expensive_qs: DjangoQuerySet[Service] = queryset.expensive_services(30000) 
        count: int = expensive_qs.count()
        message: str = f"Найдено услуг с ценой 30000 руб. или выше: {count}"
        self.message_user(request, message, level=messages.INFO)

    @admin.action(description="Названия и цены выбранных услуг (values)")
    def show_service_names_prices_values_action(self, request: HttpRequest, queryset: DjangoQuerySet[Service]) -> None:
        """Action: Показывает названия и цены выбранных услуг, используя values()."""
        services_data: DjangoQuerySet[Dict[str, Any]] = queryset.values('name', 'price')
        if services_data.exists():
            message_lines: List[str] = ["Названия и цены выбранных услуг:"]
            for service_dict in services_data:
                message_lines.append(f"- {service_dict['name']}: {service_dict['price']} руб.")
            self.message_user(request, "\n".join(message_lines), level=messages.INFO)
        else:
            self.message_user(request, "Услуги не выбраны или не найдены.", level=messages.WARNING)


@admin.register(CostCalculator)
class CostCalculatorAdmin(admin.ModelAdmin):
    """
    Конфигурация админ-панели для модели CostCalculator.
    В основном для просмотра, так как редактирование происходит через инлайн в ServiceAdmin.
    """
    list_display: Tuple[str, ...] = ('pk', 'service_link', 'base_price', 'additional_cost', 'total_cost', 'updated_at')
    list_display_links: Tuple[str, ...] = ('pk', 'service_link')
    list_filter: Tuple[str, ...] = ('updated_at',)
    search_fields: Tuple[str, ...] = ('service__name', 'pk')
    date_hierarchy: str = 'updated_at'
    raw_id_fields: Tuple[str, ...] = ('service',)
    autocomplete_fields: List[str] = ['service']
    readonly_fields: Tuple[str, ...] = ('updated_at', 'total_cost', 'pk', 'service_link', 'base_price')
    list_select_related: Tuple[str, ...] = ('service',)
    list_per_page: int = 25
    fields: Tuple[str, ...] = ('service_link', 'base_price', 'additional_cost', 'total_cost', 'updated_at')

    @admin.display(description='Услуга', ordering='service__name')
    def service_link(self, obj: CostCalculator) -> str:
        """Возвращает HTML-ссылку на связанную услугу."""
        if obj.service:
            try:
                link: str = reverse("admin:app_studio_service_change", args=[obj.service.pk])
                return format_html('<a href="{}">{}</a>', link, obj.service.name)
            except NoReverseMatch: return obj.service.name
        return "N/A"

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """
    Конфигурация админ-панели для модели Cart.
    """
    list_display: Tuple[str, ...] = ('pk', 'user_link', 'get_total_positions_display', 'get_total_items_count_display', 'get_total_cost_display', 'created_at', 'updated_at')
    list_display_links: Tuple[str, ...] = ('pk', 'user_link')
    list_filter: Tuple[str, ...] = ('created_at', 'updated_at')
    search_fields: Tuple[str, ...] = ('user__username', 'user__email', 'pk')
    date_hierarchy: str = 'updated_at'
    raw_id_fields: Tuple[str, ...] = ('user',)
    autocomplete_fields: List[str] = ['user']
    readonly_fields: Tuple[str, ...] = ('created_at', 'updated_at', 'pk', 'user_link', 'get_total_positions_display', 'get_total_items_count_display', 'get_total_cost_display')
    list_select_related: Tuple[str, ...] = ('user',)
    inlines: List[Type[admin.TabularInline]] = [CartItemInline]
    list_per_page: int = 25
    fields: Tuple[Union[str, Tuple[str, str]], ...] = ('user_link', ('created_at', 'updated_at'), ('get_total_positions_display', 'get_total_items_count_display', 'get_total_cost_display'))

    def get_queryset(self, request: HttpRequest) -> DjangoQuerySet[Cart]:
        """Аннотирует queryset данными о количестве и стоимости товаров в корзине."""
        qs: DjangoQuerySet[Cart] = super().get_queryset(request).select_related('user')
        qs = qs.annotate(
            total_items_annotated=Sum('items__quantity'),
            total_cost_annotated=Sum(F('items__quantity') * F('items__service__price')),
            total_positions_annotated=Count('items')
        )
        return qs

    @admin.display(description='Пользователь', ordering='user__username')
    def user_link(self, obj: Cart) -> str:
        """Возвращает HTML-ссылку на пользователя-владельца корзины."""
        if obj.user:
            try:
                link: str = reverse("admin:app_studio_customuser_change", args=[obj.user.pk])
                return format_html('<a href="{}">{}</a>', link, obj.user.username)
            except NoReverseMatch: return obj.user.username
        return "N/A"

    @admin.display(description='Позиций', ordering='total_positions_annotated')
    def get_total_positions_display(self, obj: Cart) -> int:
        """Возвращает количество уникальных позиций в корзине."""
        if hasattr(obj, 'total_positions_annotated') and obj.total_positions_annotated is not None: 
            return obj.total_positions_annotated 
        return obj.get_total_positions_count()

    @admin.display(description='Товаров (шт.)', ordering='total_items_annotated')
    def get_total_items_count_display(self, obj: Cart) -> int:
        """Возвращает общее количество единиц товара в корзине."""
        if hasattr(obj, 'total_items_annotated') and obj.total_items_annotated is not None: 
            return obj.total_items_annotated 
        return obj.get_total_items_count()

    @admin.display(description='Общая стоимость', ordering='total_cost_annotated')
    def get_total_cost_display(self, obj: Cart) -> str:
        """Возвращает отформатированную общую стоимость товаров в корзине."""
        cost: Union[Decimal, int] 
        if hasattr(obj, 'total_cost_annotated') and obj.total_cost_annotated is not None: 
            cost = obj.total_cost_annotated 
        else:
            cost = obj.get_total_cost() 
        return f"{cost or 0} руб."


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """
    Конфигурация админ-панели для модели CartItem.
    """
    list_display: Tuple[str, ...] = ('pk', 'cart_user_link', 'service_link', 'quantity', 'get_cost_display', 'added_at')
    list_display_links: Tuple[str, ...] = ('pk',)
    list_filter: Tuple[Union[str, Tuple[str, Type[admin.FieldListFilter]]], ...] = ('added_at', ('service', admin.RelatedOnlyFieldListFilter))
    search_fields: Tuple[str, ...] = ('cart__user__username', 'service__name', 'pk')
    date_hierarchy: str = 'added_at'
    raw_id_fields: Tuple[str, ...] = ('cart', 'service')
    autocomplete_fields: List[str] = ['cart', 'service']
    readonly_fields: Tuple[str, ...] = ('added_at', 'pk', 'cart_user_link', 'service_link', 'get_cost_display')
    list_select_related: Tuple[str, ...] = ('cart__user', 'service')
    list_per_page: int = 50
    fields: Tuple[str, ...] = ('cart', 'service', 'quantity', 'added_at')

    @admin.display(description='Пользователь', ordering='cart__user__username')
    def cart_user_link(self, obj: CartItem) -> str:
        """Возвращает HTML-ссылку на пользователя, которому принадлежит корзина."""
        if obj.cart and obj.cart.user:
            try:
                link: str = reverse("admin:app_studio_customuser_change", args=[obj.cart.user.pk])
                return format_html('<a href="{}">{}</a>', link, obj.cart.user.username)
            except NoReverseMatch: return obj.cart.user.username
        return "N/A"

    @admin.display(description='Услуга', ordering='service__name')
    def service_link(self, obj: CartItem) -> str:
        """Возвращает HTML-ссылку на услугу в элементе корзины."""
        if obj.service:
            try:
                link: str = reverse("admin:app_studio_service_change", args=[obj.service.pk])
                return format_html('<a href="{}">{}</a>', link, obj.service.name)
            except NoReverseMatch: return obj.service.name
        return "N/A"

    @admin.display(description='Стоимость', ordering='service__price')
    def get_cost_display(self, obj: CartItem) -> str:
        """Возвращает отформатированную стоимость элемента корзины."""
        return f"{obj.get_cost()} руб."

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    """
    Конфигурация админ-панели для модели Portfolio.
    """
    list_display: Tuple[str, ...] = ('pk', 'title', 'executor_link', 'image_thumbnail', 'video_link_clickable', 'uploaded_at')
    list_display_links: Tuple[str, ...] = ('pk', 'title')
    list_filter: Tuple[Union[str, Tuple[str, Type[admin.FieldListFilter]]], ...] = ('uploaded_at', ('executor', admin.RelatedOnlyFieldListFilter))
    search_fields: Tuple[str, ...] = ('executor__user__username', 'title', 'description', 'pk')
    date_hierarchy: str = 'uploaded_at'
    raw_id_fields: Tuple[str, ...] = ('executor',)
    autocomplete_fields: List[str] = ['executor']
    readonly_fields: Tuple[str, ...] = ('uploaded_at', 'pk', 'executor_link', 'video_link_clickable', 'image_thumbnail')
    list_select_related: Tuple[str, ...] = ('executor__user',)
    list_per_page: int = 25
    fields: Tuple[str, ...] = ('executor', 'title', 'image', 'image_thumbnail', 'video_link', 'description', 'uploaded_at')

    @admin.display(description='Исполнитель', ordering='executor__user__username')
    def executor_link(self, obj: Portfolio) -> str:
        """Возвращает HTML-ссылку на исполнителя работы."""
        if obj.executor and obj.executor.user:
             try:
                 link: str = reverse("admin:app_studio_executor_change", args=[obj.executor.pk])
                 return format_html('<a href="{}">{}</a>', link, obj.executor.user.username)
             except NoReverseMatch: return obj.executor.user.username
        return "N/A"

    @admin.display(description='Изображение')
    def image_thumbnail(self, obj: Portfolio) -> str:
        """Отображает миниатюру изображения работы."""
        return image_thumbnail(obj.image, width=100)

    @admin.display(description='Ссылка')
    def video_link_clickable(self, obj: Portfolio) -> str:
        """Возвращает кликабельную HTML-ссылку на видео/проект, если она есть."""
        if obj.video_link:
            return format_html('<a href="{0}" target="_blank" title="{0}">Открыть</a>', obj.video_link)
        return "Нет ссылки"


@admin.register(ExecutorService)
class ExecutorServiceAdmin(admin.ModelAdmin):
    """
    Конфигурация админ-панели для модели ExecutorService.
    """
    list_display: Tuple[str, ...] = ('pk', 'executor_link', 'service_link', 'effective_price_display', 'custom_price_display')
    list_display_links: Tuple[str, ...] = ('pk',)
    list_filter: Tuple[Any, ...] = (('custom_price', admin.EmptyFieldListFilter), ('executor', admin.RelatedOnlyFieldListFilter), ('service', admin.RelatedOnlyFieldListFilter))
    search_fields: Tuple[str, ...] = ('executor__user__username', 'service__name', 'pk')
    raw_id_fields: Tuple[str, ...] = ('executor', 'service')
    autocomplete_fields: List[str] = ['executor', 'service']
    list_select_related: Tuple[str, ...] = ('executor__user', 'service')
    list_per_page: int = 50
    readonly_fields: Tuple[str, ...] = ('pk', 'executor_link', 'service_link', 'effective_price_display')
    fields: Tuple[str, ...] = ('executor', 'service', 'custom_price')

    @admin.display(description='Исполнитель', ordering='executor__user__username')
    def executor_link(self, obj: ExecutorService) -> str:
        """Возвращает HTML-ссылку на исполнителя."""
        if obj.executor and obj.executor.user:
            try:
                link: str = reverse("admin:app_studio_executor_change", args=[obj.executor.pk])
                return format_html('<a href="{}">{}</a>', link, obj.executor.user.username)
            except NoReverseMatch: return obj.executor.user.username
        return "N/A"

    @admin.display(description='Услуга', ordering='service__name')
    def service_link(self, obj: ExecutorService) -> str:
        """Возвращает HTML-ссылку на услугу."""
        if obj.service:
             try:
                link: str = reverse("admin:app_studio_service_change", args=[obj.service.pk])
                return format_html('<a href="{}">{}</a>', link, obj.service.name)
             except NoReverseMatch: return obj.service.name
        return "N/A"

    @admin.display(description='Инд. цена', ordering='custom_price')
    def custom_price_display(self, obj: ExecutorService) -> str:
        """Отображает индивидуальную цену, если она установлена."""
        if obj.custom_price is not None:
            return f"{obj.custom_price} руб."
        return "---"

    @admin.display(description='Факт. цена', ordering='service__price')
    def effective_price_display(self, obj: ExecutorService) -> str:
        """Отображает фактическую цену услуги для данного исполнителя."""
        price: Optional[Union[Decimal, int]] = obj.get_effective_price() 
        return f"{price} руб." if price is not None else "N/A"