import io
import time
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from django.utils.html import format_html, mark_safe
from django.http import HttpResponse
from django.urls import reverse, NoReverseMatch
from django.core.files.base import ContentFile 

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportlabImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER

from .models import (
    CustomUser, Executor, OrderStatus, Order, Review, News, Message,
    Service, CostCalculator, Cart, CartItem, Portfolio, ExecutorService
)

# --- Регистрация шрифта ---
try:
    font_path = 'app_studio/fonts/DejaVuSans.ttf'
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
    print(f"Font DejaVuSans registered successfully from {font_path}")
except Exception as e:
    print(f"ERROR registering font 'DejaVuSans' from {font_path}: {e}. PDF generation might use default fonts.")

# --- Вспомогательная функция для миниатюр ---
def image_thumbnail(image_field, width=100):
    """Генерирует HTML для миниатюры ImageField."""
    if image_field:
        # Используем встроенный thumbnail если доступен или просто img тег
        return format_html('<img src="{}" width="{}" style="max-height: 100px; object-fit: contain;" />',
                           image_field.url, width)
    return "Нет фото"

# --- Кастомные фильтры ---
class OrderStatusFilter(admin.SimpleListFilter):
    title = 'Статус заказа'
    parameter_name = 'status_filter'
    def lookups(self, request, model_admin):
        statuses = OrderStatus.objects.all().order_by('pk')
        return [(status.pk, status.get_status_name_display()) for status in statuses]
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status__pk=self.value())
        return queryset

class HasCommentFilter(admin.SimpleListFilter):
    title = 'Наличие комментария'
    parameter_name = 'has_comment'
    def lookups(self, request, model_admin):
        return (('yes', 'Есть комментарий'), ('no', 'Нет комментария'))
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(comment__isnull=False).exclude(comment__exact='')
        if self.value() == 'no':
            return queryset.filter(Q(comment__isnull=True) | Q(comment__exact=''))
        return queryset

class IsAssignedFilter(admin.SimpleListFilter):
    #Фильтр для заказов: назначен исполнитель или нет
    title = 'Назначен исполнитель'
    parameter_name = 'is_assigned'
    def lookups(self, request, model_admin):
        return (('yes', 'Да'), ('no', 'Нет'))
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(executor__isnull=False)
        if self.value() == 'no':
            return queryset.filter(executor__isnull=True)
        return queryset

# --- Инлайны ---
class ExecutorServiceInline(admin.TabularInline):
    model = ExecutorService
    extra = 1
    verbose_name = "Навык/Услуга исполнителя"
    verbose_name_plural = "Навыки/Услуги исполнителя"
    raw_id_fields = ('service',)
    fields = ('service', 'custom_price') # Явный порядок
    autocomplete_fields = ['service'] # Улучшенный выбор услуги

class PortfolioInline(admin.StackedInline):
    model = Portfolio
    extra = 0
    readonly_fields = ('uploaded_at',)
    verbose_name = "Работа в портфолио"
    verbose_name_plural = "Портфолио"
    fieldsets = ( # Группировка полей для наглядности
        (None, {
            'fields': ('title', 'video_link', 'description')
        }),
        ('Метаданные', {
            'classes': ('collapse',), # Скрыть по умолчанию
            'fields': ('uploaded_at',),
        }),
    )

class ReviewInline(admin.TabularInline):
    model = Review
    fk_name = "executor"
    extra = 0
    # Показываем больше информации, но только для чтения
    readonly_fields = ('user_link', 'order_link', 'rating', 'comment_short', 'created_at')
    fields = ('user_link', 'order_link', 'rating', 'comment_short', 'created_at')
    verbose_name = "Полученный отзыв"
    verbose_name_plural = "Полученные отзывы"
    can_delete = False
    ordering = ('-created_at',)

    def has_add_permission(self, request, obj=None): return False # Запрет добавления здесь

    @admin.display(description='Автор')
    def user_link(self, obj):
        if obj.user:
            try:
                link = reverse("admin:app_studio_customuser_change", args=[obj.user.pk])
                return format_html('<a href="{}">{}</a>', link, obj.user.username)
            except NoReverseMatch: return obj.user.username
        return "N/A"

    @admin.display(description='Заказ')
    def order_link(self, obj):
        if obj.order:
             try:
                link = reverse("admin:app_studio_order_change", args=[obj.order.pk])
                return format_html('<a href="{}">Заказ #{}</a>', link, obj.order.pk)
             except NoReverseMatch: return f"Заказ #{obj.order.pk}"
        return "Без заказа"

    @admin.display(description='Комментарий')
    def comment_short(self, obj):
        return (obj.comment[:50] + '...') if obj.comment and len(obj.comment) > 50 else obj.comment

class OrderInline(admin.TabularInline):
    model = Order
    fk_name = "executor"
    extra = 0
    readonly_fields = ('order_link', 'client_link', 'service_link', 'status_colored', 'created_at', 'scheduled_at', 'is_completed')
    fields = ('order_link', 'client_link', 'service_link', 'status_colored', 'created_at', 'scheduled_at', 'is_completed')
    verbose_name = "Заказ исполнителя"
    verbose_name_plural = "Заказы исполнителя"
    can_delete = False
    ordering = ('-created_at',)
    # Добавляем select_related для оптимизации
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('client', 'service', 'status')
        return qs

    def has_add_permission(self, request, obj=None): return False # Запрет добавления здесь

    @admin.display(description='ID Заказа')
    def order_link(self, obj):
        try:
            link = reverse("admin:app_studio_order_change", args=[obj.pk])
            return format_html('<a href="{}">#{}</a>', link, obj.pk)
        except NoReverseMatch: return f"#{obj.pk}"

    @admin.display(description='Клиент')
    def client_link(self, obj): # Копия из OrderAdmin
        if obj.client:
            try:
                link = reverse("admin:app_studio_customuser_change", args=[obj.client.pk])
                return format_html('<a href="{}">{}</a>', link, obj.client.username)
            except NoReverseMatch: return obj.client.username
        return "N/A"

    @admin.display(description='Услуга')
    def service_link(self, obj): # Копия из OrderAdmin
        if obj.service:
             try:
                 link = reverse("admin:app_studio_service_change", args=[obj.service.pk])
                 return format_html('<a href="{}">{}</a>', link, obj.service.name)
             except NoReverseMatch: return obj.service.name
        return "N/A"

    @admin.display(description='Статус')
    def status_colored(self, obj): # Копия из OrderAdmin
        # код из OrderAdmin.status_colored
        if not obj.status: return "N/A"
        status_name = obj.status.status_name
        display_name = obj.status.get_status_name_display()
        color = {'new': 'blue','processing': 'orange','completed': 'green','cancelled': 'red',}.get(status_name, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, display_name)

    @admin.display(description='Завершен?', boolean=True)
    def is_completed(self, obj): # Копия из OrderAdmin
        return obj.completed_at is not None

class CostCalculatorInline(admin.StackedInline):
    model = CostCalculator
    can_delete = False
    verbose_name_plural = 'Параметры стоимости'
    fields = ('base_price', 'additional_cost', 'total_cost', 'updated_at')
    readonly_fields = ('base_price', 'total_cost', 'updated_at') # base_price тоже обновляется из услуги

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('added_at', 'get_item_cost_display', 'service_link')
    fields = ('service_link', 'quantity', 'added_at', 'get_item_cost_display')
    raw_id_fields = ('service',) # оставить услуг может быть много
    autocomplete_fields = ['service'] # Улучшенный поиск
    verbose_name = "Товар в корзине"
    verbose_name_plural = "Товары в корзине"
    ordering = ('-added_at',)

    @admin.display(description='Стоимость позиции')
    def get_item_cost_display(self, obj):
        return f"{obj.get_cost()} руб."

    @admin.display(description='Услуга')
    def service_link(self, obj):
        if obj.service:
            try:
                link = reverse("admin:app_studio_service_change", args=[obj.service.pk])
                return format_html('<a href="{}">{}</a>', link, obj.service.name)
            except NoReverseMatch: return obj.service.name
        return "N/A"

# --- Админ-классы для моделей ---
@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'get_full_name', 'phone_number', 'is_staff', 'is_active', 'date_joined', 'is_executor_display', 'avatar_thumbnail')
    list_display_links = ('username', 'email')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined', ('executor_profile', admin.EmptyFieldListFilter))
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'avatar')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'classes': ('collapse',), 'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Контактная информация и Аватар', {'fields': ('phone_number', 'first_name', 'last_name', 'email', 'avatar')}),
    )
    readonly_fields = ('last_login', 'date_joined', 'avatar_thumbnail')
    list_select_related = ('executor_profile',)
    actions = [
        'show_active_user_emails_values_list_action',
        'check_if_superuser_exists_action'
    ]

    @admin.display(description='Аватар')
    def avatar_thumbnail(self, obj): return image_thumbnail(obj.avatar, width=40)
    @admin.display(description='Исполнитель?', boolean=True)
    def is_executor_display(self, obj): return hasattr(obj, 'executor_profile') and obj.executor_profile is not None

    @admin.action(description="Email активных выбранных пользователей (values_list)")
    def show_active_user_emails_values_list_action(self, request, queryset):
        active_users_emails = queryset.filter(is_active=True).values_list('email', flat=True)
        active_emails_list = [email for email in active_users_emails if email] # Убираем None или пустые строки
        if active_emails_list:
            message = "Email выбранных активных пользователей:\n" + "\n".join(active_emails_list)
        else:
            message = "Нет активных пользователей с email среди выбранных."
        self.message_user(request, message, level='info')

    @admin.action(description="Проверить, есть ли суперюзеры в системе (exists)")
    def check_if_superuser_exists_action(self, request, queryset):
        if CustomUser.objects.filter(is_superuser=True).exists():
            message = "В системе есть как минимум один суперпользователь."
        else:
            message = "В системе нет суперпользователей."
        self.message_user(request, message, level='info')

@admin.register(Executor)
class ExecutorAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'specialization', 'experience_years', 'portfolio_link_display', 'created_at', 'portfolio_count', 'service_count')
    list_display_links = ('user_link',)
    list_filter = ('specialization', 'experience_years', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialization', 'pk')
    inlines = [ExecutorServiceInline, PortfolioInline, ReviewInline] # OrderInline, может быть много
    date_hierarchy = 'created_at'
    raw_id_fields = ('user',)
    autocomplete_fields = ['user'] # Улучшенный выбор пользователя
    readonly_fields = ('created_at', 'user_link', 'portfolio_count', 'service_count')
    list_select_related = ('user',)
    list_prefetch_related = ('portfolios', 'services') # Для подсчета в list_display
    list_per_page = 20
    fieldsets = ( # Группировка полей в форме редактирования
        (None, {'fields': ('user_link', 'specialization', 'experience_years', 'portfolio_link')}),
        ('Метаданные', {'classes': ('collapse',), 'fields': ('created_at',)})
    )

    @admin.display(description='Пользователь', ordering='user__username')
    def user_link(self, obj):
        if obj.user:
            try:
                link = reverse("admin:app_studio_customuser_change", args=[obj.user.pk])
                return format_html('<a href="{}">{}</a>', link, obj.user.username)
            except NoReverseMatch: return obj.user.username
        return "N/A"

    @admin.display(description='Портфолио')
    def portfolio_link_display(self, obj):
        if obj.portfolio_link:
            return format_html('<a href="{0}" target="_blank" title="{0}">Ссылка</a>', obj.portfolio_link)
        return "Нет ссылки"

    # Оптимизированные подсчеты через prefetch
    @admin.display(description='Работ в портфолио')
    def portfolio_count(self, obj):
        return obj.portfolios.count() # Работает быстро из-за prefetch_related

    @admin.display(description='Услуг')
    def service_count(self, obj):
        return obj.services.count()


@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ('pk', 'status_name', 'get_display_name', 'order_count')
    search_fields = ('status_name',)
    readonly_fields = ('pk', 'order_count')
    fields = ('status_name',) 

    @admin.display(description='Отображаемое имя')
    def get_display_name(self, obj):
        return obj.get_status_name_display()

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(order_count_annotated=Count('orders'))
        return queryset

    @admin.display(description='Кол-во заказов', ordering='order_count_annotated')
    def order_count(self, obj):
        return obj.order_count_annotated


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('pk', 'client_link', 'executor_link', 'service_link', 'status_colored', 'created_at', 'scheduled_at', 'is_completed')
    list_display_links = ('pk',) # Ссылка по ID
    list_filter = (OrderStatusFilter, IsAssignedFilter, 'created_at', 'scheduled_at', 'completed_at', ('client', admin.RelatedOnlyFieldListFilter), ('executor', admin.RelatedOnlyFieldListFilter), ('service', admin.RelatedOnlyFieldListFilter)) # Больше фильтров!
    search_fields = ('client__username', 'executor__user__username', 'service__name', 'pk')
    date_hierarchy = 'created_at'
    raw_id_fields = ('client', 'executor', 'service', 'status')
    autocomplete_fields = ['client', 'executor', 'service', 'status'] # Улучшенный поиск
    readonly_fields = ('created_at', 'pk')
    list_select_related = ('client', 'executor__user', 'service', 'status')
    actions = ['mark_completed', 'mark_processing', 'generate_order_pdf']
    list_per_page = 25
    fieldsets = ( # Группировка полей в форме
        ('Основная информация', {'fields': ('client', 'service', 'executor', 'status')}),
        ('Даты', {'fields': ('created_at', 'scheduled_at', 'completed_at')}),
    )

    @admin.display(description='Клиент', ordering='client__username')
    def client_link(self, obj):
        if obj.client:
            try:
                link = reverse("admin:app_studio_customuser_change", args=[obj.client.pk])
                return format_html('<a href="{}">{}</a>', link, obj.client.username)
            except NoReverseMatch: return obj.client.username
        return "Клиент удален"

    @admin.display(description='Исполнитель', ordering='executor__user__username')
    def executor_link(self, obj):
        if obj.executor and obj.executor.user:
             try:
                link = reverse("admin:app_studio_executor_change", args=[obj.executor.pk])
                return format_html('<a href="{}">{}</a>', link, obj.executor.user.username)
             except NoReverseMatch: return obj.executor.user.username
        elif obj.executor:
             return "Профиль исполнителя есть, но пользователь удален?" # Странная ситуация
        return "Не назначен"

    @admin.display(description='Услуга', ordering='service__name')
    def service_link(self, obj):
        if obj.service:
             try:
                 link = reverse("admin:app_studio_service_change", args=[obj.service.pk])
                 return format_html('<a href="{}">{}</a>', link, obj.service.name)
             except NoReverseMatch: return obj.service.name
        return "Услуга удалена"

    @admin.display(description='Статус', ordering='status__status_name')
    def status_colored(self, obj):
        if not obj.status: return "N/A"
        status_name = obj.status.status_name
        display_name = obj.status.get_status_name_display()
        color = {'new': 'blue','processing': 'orange','completed': 'green','cancelled': 'red',}.get(status_name, 'black')
        # Используем CSS классы для лучшей кастомизации 
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, display_name)

    @admin.display(description='Завершен?', boolean=True, ordering='completed_at')
    def is_completed(self, obj):
        return obj.completed_at is not None

    @admin.action(description='Отметить как "В обработке"')
    def mark_processing(self, request, queryset):
        try:
            status_processing = OrderStatus.objects.get(status_name='processing')
            updated_count = queryset.update(status=status_processing, completed_at=None) # Сбрасывает дату завершения
            self.message_user(request, f"Статус 'В обработке' установлен для {updated_count} заказов.")
        except OrderStatus.DoesNotExist:
            self.message_user(request, "Ошибка: Статус 'В обработке' не найден.", level='error')
        except Exception as e:
             self.message_user(request, f"Произошла ошибка: {e}", level='error')

    @admin.action(description='Отметить как "Выполнен"')
    def mark_completed(self, request, queryset):
        queryset_to_update = queryset.exclude(status__status_name__in=['completed', 'cancelled'])
        try:
            status_completed = OrderStatus.objects.get(status_name='completed')
            now = timezone.now()
            updated_count = queryset_to_update.update(status=status_completed, completed_at=now)
            self.message_user(request, f"Статус 'Выполнен' установлен для {updated_count} заказов.")
        except OrderStatus.DoesNotExist:
            self.message_user(request, "Ошибка: Статус 'Выполнен' не найден.", level='error')
        except Exception as e:
             self.message_user(request, f"Произошла ошибка: {e}", level='error')


    @admin.action(description='Сгенерировать PDF для выбранных заказов')
    def generate_order_pdf(self, request, queryset):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        styles['Normal'].fontName = 'DejaVuSans'
        styles['Heading1'].fontName = 'DejaVuSans'
        styles['Heading2'].fontName = 'DejaVuSans'
        story = []
        story.append(Paragraph("Отчет по заказам", styles['h1']))
        story.append(Spacer(1, 1*cm))
        for order in queryset.select_related('client', 'executor__user', 'service', 'status'):
             story.append(Paragraph(f"<u>Заказ #{order.pk}</u>", styles['h2']))
             story.append(Spacer(1, 0.2*cm))
             client = order.client.get_full_name() or order.client.username if order.client else 'Удален'
             executor = order.executor.user.get_full_name() or order.executor.user.username if order.executor and order.executor.user else 'Не назначен/Удален'
             service = order.service.name if order.service else 'Удалена'
             status = order.status.get_status_name_display() if order.status else 'Неизвестен'
             created = order.created_at.strftime('%d.%m.%Y %H:%M') if order.created_at else '-'
             scheduled = order.scheduled_at.strftime('%d.%m.%Y %H:%M') if order.scheduled_at else '-'
             completed = order.completed_at.strftime('%d.%m.%Y %H:%M') if order.completed_at else '-'
             details = [ f"<b>Клиент:</b> {client}", f"<b>Исполнитель:</b> {executor}", f"<b>Услуга:</b> {service}", f"<b>Статус:</b> {status}", f"<b>Создан:</b> {created}", f"<b>План. время:</b> {scheduled}", f"<b>Завершен:</b> {completed}",]
             for detail in details: story.append(Paragraph(detail, styles['Normal']))
             story.append(Spacer(1, 0.5*cm))
        try: doc.build(story)
        except Exception as e: return HttpResponse(f"Ошибка генерации PDF: {e}", status=500)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="orders_report.pdf"'
        return response




@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user_link', 'executor_link', 'order_link', 'rating_stars', 'comment_short', 'created_at')
    list_display_links = ('pk',)
    list_filter = ('rating', 'created_at', HasCommentFilter, ('user', admin.RelatedOnlyFieldListFilter), ('executor', admin.RelatedOnlyFieldListFilter), ('order', admin.RelatedOnlyFieldListFilter))
    search_fields = ('user__username', 'executor__user__username', 'comment', 'pk', 'order__pk')
    date_hierarchy = 'created_at'
    # autocomplete для удобного выбора связей
    raw_id_fields = ('user', 'executor', 'order')
    autocomplete_fields = ['user', 'executor', 'order']
    list_select_related = ('user', 'executor__user', 'order')
    list_per_page = 25

    fields = ('user', 'executor', 'order', 'rating', 'comment', 'created_at')

    readonly_fields = ('created_at',)

    def get_form(self, request, obj=None, **kwargs):
        # Получает стандартную форму
        form = super().get_form(request, obj, **kwargs)
        # Изменяет queryset для поля user в этой форме
        if 'user' in form.base_fields:
            form.base_fields['user'].queryset = CustomUser.objects.filter(
                executor_profile__isnull=True # Только пользователи без профиля исполнителя
            ).order_by('username')
        return form

    
    # --- Методы для ОТОБРАЖЕНИЯ В СПИСКЕ (list_display) ---
    @admin.display(description='Автор', ordering='user__username')
    def user_link(self, obj):
        if obj.user:
            try:
                link = reverse("admin:app_studio_customuser_change", args=[obj.user.pk])
                return format_html('<a href="{}">{}</a>', link, obj.user.username)
            except NoReverseMatch: return obj.user.username
        return "N/A"

    @admin.display(description='Исполнитель', ordering='executor__user__username')
    def executor_link(self, obj):
        if obj.executor and obj.executor.user:
            try:
                link = reverse("admin:app_studio_executor_change", args=[obj.executor.pk])
                return format_html('<a href="{}">{}</a>', link, obj.executor.user.username)
            except NoReverseMatch: return obj.executor.user.username
        return "N/A"

    @admin.display(description='Заказ', ordering='order__pk')
    def order_link(self, obj):
        if obj.order:
             try:
                link = reverse("admin:app_studio_order_change", args=[obj.order.pk])
                return format_html('<a href="{}">Заказ #{}</a>', link, obj.order.pk)
             except NoReverseMatch: return f"Заказ #{obj.order.pk}"
        return "Без заказа" 

    @admin.display(description='Оценка', ordering='rating')
    def rating_stars(self, obj):
        if obj and obj.rating is not None:
            try:
                rating_value = int(obj.rating)
                if 1 <= rating_value <= 5:
                    stars = '★' * rating_value + '☆' * (5 - rating_value)
                    return mark_safe(f'<span style="font-size: 1.2em; color: orange;">{stars}</span>')
                else: return f"Рейт.: {obj.rating}"
            except (ValueError, TypeError): return "?"
        return "---" # Если рейтинг не задан в списке

    @admin.display(description='Комментарий')
    def comment_short(self, obj):
         return (obj.comment[:50] + '...') if obj.comment and len(obj.comment) > 50 else obj.comment

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'author_link', 'published_at', 'pdf_link_display', 'content_preview')
    list_display_links = ('pk', 'title')
    list_filter = ('published_at', ('author', admin.RelatedOnlyFieldListFilter))
    search_fields = ('title', 'content', 'author__username', 'pk')
    date_hierarchy = 'published_at'
    raw_id_fields = ('author',)
    autocomplete_fields = ['author']
    readonly_fields = ('published_at', 'pk', 'author_link', 'pdf_link_display')
    actions = ['generate_news_pdf_action', 'find_news_with_exact_case_word_action']
    list_per_page = 20
    list_select_related = ('author',)
    fieldsets = (
        (None, {'fields': ('title', 'content')}),
        ('Метаданные', {'fields': ('author', 'pdf_file', 'pdf_link_display', 'published_at')}),
    )
    @admin.display(description='Автор', ordering='author__username')
    def author_link(self, obj):
        if obj.author:
            try: return format_html('<a href="{}">{}</a>', reverse("admin:app_studio_customuser_change", args=[obj.author.pk]), obj.author.username)
            except NoReverseMatch: return obj.author.username
        return "Автор не указан/удален"
    @admin.display(description='PDF файл')
    def pdf_link_display(self, obj):
        if obj.pdf_file: return format_html('<a href="{}" target="_blank">Скачать/Просмотреть</a>', obj.pdf_file.url)
        return "Нет файла"
    @admin.display(description='Начало текста')
    def content_preview(self, obj):
        return (obj.content[:100] + '...') if obj.content and len(obj.content) > 100 else obj.content
    @admin.action(description='Сгенерировать PDF и (если 1) сохранить')
    def generate_news_pdf_action(self, request, queryset):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        styles['Normal'].fontName = 'DejaVuSans'; styles['Normal'].fontSize = 11; styles['Normal'].leading = 14; styles['Normal'].alignment = TA_JUSTIFY
        styles['Heading1'].fontName = 'DejaVuSans'; styles['Heading1'].fontSize = 16; styles['Heading1'].alignment = TA_CENTER; styles['Heading1'].spaceAfter = 0.5*cm
        styles['Heading2'].fontName = 'DejaVuSans'; styles['Heading2'].fontSize = 14; styles['Heading2'].spaceBefore = 0.5*cm; styles['Heading2'].spaceAfter = 0.3*cm
        story = [Paragraph("Дайджест новостей" if queryset.count() > 1 else f"Новость: {queryset.first().title}", styles['h1'])]
        for news in queryset.select_related('author'):
            story.extend([
                Paragraph(news.title, styles['h2']),
                Paragraph(f"<i>Автор: {news.author.username if news.author else 'Неизвестный автор'}, Опубликовано: {news.published_at.strftime('%d.%m.%Y') if news.published_at else '-'}</i>", styles['Normal']),
                Spacer(1, 0.2*cm)
            ])
            for paragraph_text in news.content.split('\n'):
                if paragraph_text.strip(): story.append(Paragraph(paragraph_text, styles['Normal']))
            story.append(Spacer(1, 0.8*cm))
        try: doc.build(story)
        except Exception as e: self.message_user(request, f"Ошибка генерации PDF: {e}", level='error'); return
        pdf_content = buffer.getvalue(); buffer.close()
        if queryset.count() == 1:
            news_item = queryset.first()
            try:
                filename = f"news_{news_item.pk}_{int(time.time())}.pdf"
                news_item.pdf_file.save(filename, ContentFile(pdf_content), save=True)
                self.message_user(request, f"PDF для новости '{news_item.title}' сгенерирован и сохранен.", level='success')
            except Exception as e: self.message_user(request, f"PDF сгенерирован, ошибка сохранения: {e}", level='warning')
        elif queryset.count() > 1: self.message_user(request, f"PDF-дайджест для {queryset.count()} новостей сгенерирован.", level='info')
        else: self.message_user(request, "Не выбрано новостей.", level='warning'); return
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{"news_report.pdf" if queryset.count() > 1 else f"news_{queryset.first().pk}.pdf"}"'
        return response

    @admin.action(description="Найти новости со словом 'Django' (регистрозависимо, __contains)")
    def find_news_with_exact_case_word_action(self, request, queryset):
        news_with_word = queryset.filter(title__contains='Django') # <-- Использование __contains
        if news_with_word.exists():
            titles = news_with_word.values_list('title', flat=True)
            message = "Новости, содержащие 'Django' (с учетом регистра) в заголовке:\n" + "\n".join(titles)
            self.message_user(request, message, level='info')
        else:
            self.message_user(request, "Не найдено новостей с точным вхождением 'Django' в заголовке среди выбранных.", level='info')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('pk', 'sender_link', 'receiver_link', 'content_short', 'sent_at', 'is_read')
    list_display_links = ('pk',)
    list_filter = ('sent_at', 'is_read', ('sender', admin.RelatedOnlyFieldListFilter), ('receiver', admin.RelatedOnlyFieldListFilter))
    search_fields = ('sender__username', 'receiver__username', 'content', 'pk')
    date_hierarchy = 'sent_at'
    raw_id_fields = ('sender', 'receiver')
    autocomplete_fields = ['sender', 'receiver']
    readonly_fields = ('sent_at', 'pk', 'sender_link', 'receiver_link')
    list_select_related = ('sender', 'receiver')
    list_per_page = 30
    actions = ['mark_as_read', 'mark_as_unread']
    fields = ('sender_link', 'receiver_link', 'sent_at', 'is_read', 'content')

    @admin.display(description='Отправитель', ordering='sender__username')
    def sender_link(self, obj):
        if obj.sender:
            try:
                link = reverse("admin:app_studio_customuser_change", args=[obj.sender.pk])
                return format_html('<a href="{}">{}</a>', link, obj.sender.username)
            except NoReverseMatch: return obj.sender.username
        return "N/A"


    @admin.display(description='Получатель', ordering='receiver__username')
    def receiver_link(self, obj):
        if obj.receiver:
             try:
                link = reverse("admin:app_studio_customuser_change", args=[obj.receiver.pk])
                return format_html('<a href="{}">{}</a>', link, obj.receiver.username)
             except NoReverseMatch: return obj.receiver.username
        return "N/A"


    @admin.display(description='Содержимое')
    def content_short(self, obj):
        return (obj.content[:75] + '...') if obj.content and len(obj.content) > 75 else obj.content

    @admin.action(description='Отметить как прочитанные')
    def mark_as_read(self, request, queryset): # Копия
        updated_count = queryset.update(is_read=True)
        self.message_user(request, f"{updated_count} сообщений отмечены как прочитанные.")

    @admin.action(description='Отметить как непрочитанные')
    def mark_as_unread(self, request, queryset): # Копия
        updated_count = queryset.update(is_read=False)
        self.message_user(request, f"{updated_count} сообщений отмечены как непрочитанные.")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('pk', 'thumbnail', 'name', 'price', 'total_cost_display', 'duration_hours', 'created_at', 'order_count_display', 'executor_count_display')
    list_display_links = ('pk', 'name')
    list_filter = ('created_at',)
    search_fields = ('name', 'description', 'pk')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'pk', 'thumbnail', 'order_count_display', 'executor_count_display', 'total_cost_display')
    inlines = [CostCalculatorInline]
    actions = [
        'show_service_order_count', 
        'show_expensive_service_count',
        'show_service_names_prices_values_action'
        ]
    list_per_page = 20
    list_select_related = ('cost_calculator',)
    fieldsets = (
        (None, {'fields': ('name', 'description', 'price', 'duration_hours')}),
        ('Изображение', {'fields': ('photo', 'thumbnail')}),
        ('Метаданные', {'classes': ('collapse',), 'fields': ('created_at',)}),
    )
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cost_calculator').annotate(
            order_count_annotated=Count('orders', distinct=True),
            executor_count_annotated=Count('executors', distinct=True)
        )
    @admin.display(description='Миниатюра')
    def thumbnail(self, obj): return image_thumbnail(obj.photo, width=80)
    @admin.display(description='Итоговая цена', ordering='cost_calculator__total_cost')
    def total_cost_display(self, obj):
        if hasattr(obj, 'cost_calculator') and obj.cost_calculator: return f"{obj.cost_calculator.total_cost} руб."
        return f"{obj.price} руб. (базовая)" if obj.price is not None else "N/A"
    @admin.display(description='Кол-во заказов', ordering='order_count_annotated')
    def order_count_display(self, obj): return obj.order_count_annotated
    @admin.display(description='Кол-во исполнителей', ordering='executor_count_annotated')
    def executor_count_display(self, obj): return obj.executor_count_annotated
    @admin.action(description="Показать количество заказов для выбранных услуг")
    def show_service_order_count(self, request, queryset): 
        message_lines = ["Количество заказов для выбранных услуг:"]
        for service in queryset.annotate(order_count=Count('orders', distinct=True)):
            message_lines.append(f"- {service.name}: {service.order_count}")
        self.message_user(request, "\n".join(message_lines), level='info')
    @admin.action(description="Показать кол-во услуг с ценой >= 30000")
    def show_expensive_service_count(self, request, queryset): 
        count = queryset.expensive_services(30000).count()
        self.message_user(request, f"Найдено услуг с ценой 30000 руб. или выше: {count}", level='info')
    
    @admin.action(description="Названия и цены выбранных услуг (values)")
    def show_service_names_prices_values_action(self, request, queryset):
        services_data = queryset.values('name', 'price') # <-- Использование values()
        if services_data:
            message_lines = ["Названия и цены выбранных услуг:"]
            for service_dict in services_data:
                message_lines.append(f"- {service_dict['name']}: {service_dict['price']} руб.")
            self.message_user(request, "\n".join(message_lines), level='info')
        else:
            self.message_user(request, "Услуги не выбраны или не найдены.", level='warning')


@admin.register(CostCalculator)
class CostCalculatorAdmin(admin.ModelAdmin):
    # Эта модель в основном редактируется через инлайн в ServiceAdmin
    # Отдельный список полезен для обзора или массовых действий
    list_display = ('pk', 'service_link', 'base_price', 'additional_cost', 'total_cost', 'updated_at')
    list_display_links = ('pk', 'service_link')
    list_filter = ('updated_at',)
    search_fields = ('service__name', 'pk')
    date_hierarchy = 'updated_at'
    raw_id_fields = ('service',)
    autocomplete_fields = ['service']
    readonly_fields = ('updated_at', 'total_cost', 'pk', 'service_link', 'base_price')
    list_select_related = ('service',)
    list_per_page = 25
    fields = ('service_link', 'base_price', 'additional_cost', 'total_cost', 'updated_at')

    @admin.display(description='Услуга', ordering='service__name')
    def service_link(self, obj): 
        if obj.service:
            try:
                link = reverse("admin:app_studio_service_change", args=[obj.service.pk])
                return format_html('<a href="{}">{}</a>', link, obj.service.name)
            except NoReverseMatch: return obj.service.name
        return "N/A"

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user_link', 'get_total_positions_display', 'get_total_items_count_display', 'get_total_cost_display', 'created_at', 'updated_at')
    list_display_links = ('pk', 'user_link')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'pk')
    date_hierarchy = 'updated_at'
    raw_id_fields = ('user',)
    autocomplete_fields = ['user']
    readonly_fields = ('created_at', 'updated_at', 'pk', 'user_link', 'get_total_positions_display', 'get_total_items_count_display', 'get_total_cost_display')
    list_select_related = ('user',)
    inlines = [CartItemInline]
    list_per_page = 25
    fields = ('user_link', ('created_at', 'updated_at'), ('get_total_positions_display', 'get_total_items_count_display', 'get_total_cost_display')) # Структура в форме

    # Используем аннотации для сортировки и эффективности
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('user')
        qs = qs.annotate(
            total_items_annotated=Sum('items__quantity'),
            total_cost_annotated=Sum(F('items__quantity') * F('items__service__price')),
            total_positions_annotated=Count('items')
        )
        return qs

    @admin.display(description='Пользователь', ordering='user__username')
    def user_link(self, obj):
        if obj.user:
            try:
                link = reverse("admin:app_studio_customuser_change", args=[obj.user.pk])
                return format_html('<a href="{}">{}</a>', link, obj.user.username)
            except NoReverseMatch: return obj.user.username
        return "N/A"

    @admin.display(description='Позиций', ordering='total_positions_annotated')
    def get_total_positions_display(self, obj):
        # Используем аннотированное значение, если доступно
        if hasattr(obj, 'total_positions_annotated'):
            return obj.total_positions_annotated or 0
        return obj.get_total_positions_count()

    @admin.display(description='Товаров (шт.)', ordering='total_items_annotated')
    def get_total_items_count_display(self, obj):
        if hasattr(obj, 'total_items_annotated'):
            return obj.total_items_annotated or 0
        return obj.get_total_items_count()

    @admin.display(description='Общая стоимость', ordering='total_cost_annotated')
    def get_total_cost_display(self, obj):
        if hasattr(obj, 'total_cost_annotated'):
            cost = obj.total_cost_annotated or 0
        else:
            cost = obj.get_total_cost()
        return f"{cost} руб."

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('pk', 'cart_user_link', 'service_link', 'quantity', 'get_cost_display', 'added_at')
    list_display_links = ('pk',)
    list_filter = ('added_at', ('service', admin.RelatedOnlyFieldListFilter)) # Фильтр по услуге
    search_fields = ('cart__user__username', 'service__name', 'pk')
    date_hierarchy = 'added_at'
    raw_id_fields = ('cart', 'service')
    autocomplete_fields = ['cart', 'service']
    readonly_fields = ('added_at', 'pk', 'cart_user_link', 'service_link', 'get_cost_display')
    list_select_related = ('cart__user', 'service')
    list_per_page = 50
    fields = ('cart', 'service', 'quantity', 'added_at')

    @admin.display(description='Пользователь', ordering='cart__user__username')
    def cart_user_link(self, obj):
         if obj.cart and obj.cart.user:
            try:
                link = reverse("admin:app_studio_customuser_change", args=[obj.cart.user.pk])
                return format_html('<a href="{}">{}</a>', link, obj.cart.user.username)
            except NoReverseMatch: return obj.cart.user.username
         return "N/A"

    @admin.display(description='Услуга', ordering='service__name')
    def service_link(self, obj):
        if obj.service:
            try:
                link = reverse("admin:app_studio_service_change", args=[obj.service.pk])
                return format_html('<a href="{}">{}</a>', link, obj.service.name)
            except NoReverseMatch: return obj.service.name
        return "N/A"

    @admin.display(description='Стоимость', ordering='service__price')
    def get_cost_display(self, obj):
        return f"{obj.get_cost()} руб."

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'executor_link', 'image_thumbnail', 'video_link_clickable', 'uploaded_at')
    list_display_links = ('pk', 'title')
    list_filter = ('uploaded_at', ('executor', admin.RelatedOnlyFieldListFilter))
    search_fields = ('executor__user__username', 'title', 'description', 'pk')
    date_hierarchy = 'uploaded_at'
    raw_id_fields = ('executor',)
    autocomplete_fields = ['executor']
    readonly_fields = ('uploaded_at', 'pk', 'executor_link', 'video_link_clickable', 'image_thumbnail')
    list_select_related = ('executor__user',)
    list_per_page = 25
    fields = ('executor', 'title', 'image', 'image_thumbnail', 'video_link', 'description', 'uploaded_at')

    @admin.display(description='Исполнитель', ordering='executor__user__username')
    def executor_link(self, obj):
        if obj.executor and obj.executor.user:
             try:
                 link = reverse("admin:app_studio_executor_change", args=[obj.executor.pk])
                 return format_html('<a href="{}">{}</a>', link, obj.executor.user.username)
             except NoReverseMatch: return obj.executor.user.username
        return "N/A"

    @admin.display(description='Изображение')
    def image_thumbnail(self, obj):
        return image_thumbnail(obj.image, width=100)

    @admin.display(description='Ссылка')
    def video_link_clickable(self, obj):
        if obj.video_link:
            return format_html('<a href="{0}" target="_blank" title="{0}">Открыть</a>', obj.video_link)
        return "Нет ссылки"


@admin.register(ExecutorService)
class ExecutorServiceAdmin(admin.ModelAdmin):
    list_display = ('pk', 'executor_link', 'service_link', 'effective_price_display', 'custom_price_display')
    list_display_links = ('pk',)
    list_filter = (('custom_price', admin.EmptyFieldListFilter), ('executor', admin.RelatedOnlyFieldListFilter), ('service', admin.RelatedOnlyFieldListFilter))
    search_fields = ('executor__user__username', 'service__name', 'pk')
    raw_id_fields = ('executor', 'service')
    autocomplete_fields = ['executor', 'service']
    list_select_related = ('executor__user', 'service')
    list_per_page = 50
    readonly_fields = ('pk', 'executor_link', 'service_link', 'effective_price_display')
    fields = ('executor', 'service', 'custom_price')

    @admin.display(description='Исполнитель', ordering='executor__user__username')
    def executor_link(self, obj):
        if obj.executor and obj.executor.user:
            try:
                link = reverse("admin:app_studio_executor_change", args=[obj.executor.pk])
                return format_html('<a href="{}">{}</a>', link, obj.executor.user.username)
            except NoReverseMatch: return obj.executor.user.username
        return "N/A"

    @admin.display(description='Услуга', ordering='service__name')
    def service_link(self, obj):
        if obj.service:
             try:
                link = reverse("admin:app_studio_service_change", args=[obj.service.pk])
                return format_html('<a href="{}">{}</a>', link, obj.service.name)
             except NoReverseMatch: return obj.service.name
        return "N/A"

    @admin.display(description='Инд. цена', ordering='custom_price')
    def custom_price_display(self, obj):
        if obj.custom_price is not None:
            return f"{obj.custom_price} руб."
        return "---" #прочерк для отсутствия

    @admin.display(description='Факт. цена', ordering='service__price') # Примерная сортировка по базовой
    def effective_price_display(self, obj):
        price = obj.get_effective_price()
        return f"{price} руб."