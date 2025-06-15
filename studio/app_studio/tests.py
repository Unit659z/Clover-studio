from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase 
from django.contrib.auth import get_user_model

from .models import (
    Service,
    OrderStatus,
    Order,
    Executor,
    Portfolio,
    News,
    Review,
    Cart,
    CartItem,
)

CustomUser = get_user_model()

class BaseAPITestCase(APITestCase):
    """
    Базовый класс для API тестов с общими методами setup.
    """
    def setUp(self):
        # --- Создаем пользователей ---
        self.admin_user = CustomUser.objects.create_superuser(
            username='testadmin',
            email='admin@example.com',
            password='testpassword123'
        )
        self.client_user = CustomUser.objects.create_user(
            username='testclient',
            email='client@example.com',
            password='testpassword123',
            first_name='Client',
            last_name='User'
        )
        self.executor_user_data = {
            'username': 'testexecutor',
            'email': 'executor@example.com',
            'password': 'testpassword123',
            'first_name': 'Executor',
            'last_name': 'Person'
        }
        self.executor_user = CustomUser.objects.create_user(**self.executor_user_data)

        # --- Создаем исполнителя ---
        self.executor_profile = Executor.objects.create(
            user=self.executor_user,
            specialization="Видеомонтаж",
            experience_years=5
        )

        # --- Создаем статус заказа ---
        self.status_new, _ = OrderStatus.objects.get_or_create(status_name='new')
        self.status_completed, _ = OrderStatus.objects.get_or_create(status_name='completed')

        # --- Создаем услугу ---
        self.service1 = Service.objects.create(
            name="Тестовый Видеомонтаж",
            description="Описание тестового видеомонтажа",
            price=10000.00,
            duration_hours=10
        )
        self.service2 = Service.objects.create(
            name="Тестовая Цветокоррекция",
            description="Описание тестовой цветокоррекции",
            price=5000.00,
            duration_hours=5
        )
        self.executor_profile.services.add(self.service1)


# --- Тесты Моделей ---
class ModelTests(BaseAPITestCase):

    def test_custom_user_str(self): # ТЕСТ 1
        """Тест строкового представления CustomUser."""
        self.assertEqual(str(self.client_user), "Client User (testclient)")
        user_no_name = CustomUser.objects.create_user(username='nonameuser', email='noname@example.com')
        self.assertEqual(str(user_no_name), "noname@example.com")

    def test_service_str(self): # ТЕСТ 2
        """Тест строкового представления Service."""
        self.assertEqual(str(self.service1), "Тестовый Видеомонтаж")

    def test_order_creation_default_status(self): # ТЕСТ 3
        """Тест создания заказа и назначения статуса (логика из OrderWriteSerializer)."""
        order = Order.objects.create(
            client=self.client_user,
            service=self.service1,
            status=self.status_new 
        )
        self.assertEqual(order.status.status_name, 'new')
        self.assertTrue(Order.objects.filter(pk=order.pk).exists())


# --- Тесты API Эндпоинтов ---
class ServiceAPITests(BaseAPITestCase):

    def test_list_services_unauthenticated(self): # ТЕСТ 4
        """Тест получения списка услуг без аутентификации."""
        url = reverse('app_studio:service-api-list') 
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 2) 

    def test_create_service_authenticated_admin(self): # ТЕСТ 5
        """Тест создания услуги администратором."""
        url = reverse('app_studio:service-api-list')
        self.client.login(username='testadmin', password='testpassword123')
        data = {
            "name": "Новая услуга от Админа",
            "description": "Супер описание",
            "price": "12345.00",
            "duration_hours": 8
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Service.objects.count(), 3)
        self.assertEqual(response.data['name'], "Новая услуга от Админа")
        new_service = Service.objects.get(pk=response.data['pk'])
        self.assertTrue(hasattr(new_service, 'cost_calculator'))
        self.assertEqual(new_service.cost_calculator.base_price, new_service.price)


    def test_create_service_unauthorized_client(self): # ТЕСТ 6
        """Тест попытки создания услуги обычным клиентом (должен быть запрет)."""
        url = reverse('app_studio:service-api-list')
        self.client.login(username='testclient', password='testpassword123')
        data = {
            "name": "Услуга от Клиента",
            "description": "Описание",
            "price": "100.00",
            "duration_hours": 1
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class PortfolioAPITests(BaseAPITestCase):

    def setUp(self):
        super().setUp()
        self.portfolio_item1 = Portfolio.objects.create(
            executor=self.executor_profile,
            title="Работа в портфолио 1",
            description="Описание работы 1"
        )

    def test_list_portfolio_items(self): # ТЕСТ 7
        """Тест получения списка работ портфолио."""
        url = reverse('app_studio:portfolio-api-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "Работа в портфолио 1")

    def test_create_portfolio_item_by_executor(self): # ТЕСТ 8
        """Тест создания работы в портфолио самим исполнителем."""
        url = reverse('app_studio:portfolio-api-list')
        self.client.login(username='testexecutor', password='testpassword123')
        data = {
            "title": "Новая работа исполнителя",
            "description": "Это моя новая работа",
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], "Новая работа исполнителя")
        self.assertEqual(response.data['executor']['pk'], self.executor_profile.pk)


class OrderAPITests(BaseAPITestCase):

    def test_create_order_by_client(self): # ТЕСТ 9
        """Тест создания заказа аутентифицированным клиентом."""
        url = reverse('app_studio:order-api-list')
        self.client.login(username='testclient', password='testpassword123')
        data = {
            "service": self.service1.pk,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        created_order = Order.objects.first()
        self.assertEqual(created_order.client, self.client_user)
        self.assertEqual(created_order.service, self.service1)
        self.assertEqual(created_order.status.status_name, 'new')

    def test_list_orders_for_client(self): # ТЕСТ 10
        """Тест: клиент видит только свои заказы."""
        Order.objects.create(client=self.client_user, service=self.service1, status=self.status_new)
        other_user = CustomUser.objects.create_user(username='otherclient', password='password')
        Order.objects.create(client=other_user, service=self.service2, status=self.status_new)

        url = reverse('app_studio:order-api-list')
        self.client.login(username='testclient', password='testpassword123')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1) 
        self.assertEqual(response.data['results'][0]['client']['pk'], self.client_user.pk)

    def test_order_mark_as_completed_by_executor(self): # ТЕСТ 11
        """Тест: исполнитель может пометить свой заказ как выполненный."""
        order = Order.objects.create(
            client=self.client_user,
            service=self.service1,
            executor=self.executor_profile,
            status=self.status_new
        )
        url = reverse('app_studio:order-api-mark-as-completed', kwargs={'pk': order.pk})
        self.client.login(username='testexecutor', password='testpassword123') 
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, self.status_completed)
        self.assertIsNotNone(order.completed_at)

class NewsAPITests(BaseAPITestCase):
    def test_create_news_by_admin(self): # ТЕСТ 12
        """Тест создания новости администратором."""
        url = reverse('app_studio:news-api-list')
        self.client.login(username='testadmin', password='testpassword123')
        data = {
            "title": "Супер Новость от Админа",
            "content": "Очень важный контент новости."
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(News.objects.count(), 1)
        self.assertEqual(response.data['title'], "Супер Новость от Админа")
        self.assertEqual(response.data['author']['pk'], self.admin_user.pk) 



