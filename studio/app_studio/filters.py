import django_filters
from .models import Service

class ServiceFilter(django_filters.FilterSet):
    """
    Кастомный FilterSet для модели Service.

    Позволяет фильтровать услуги по диапазону цен и длительности.
    """

    price__gte = django_filters.NumberFilter(
        field_name='price', 
        lookup_expr='gte',
        label='Цена от'
    )

    price__lte = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        label='Цена до'
    )

    duration_hours = django_filters.RangeFilter(
        label='Длительность (в часах, диапазон)'
    )

    class Meta:
        model = Service
        fields = ['price', 'duration_hours']