

import random
from datetime import timedelta
from django.utils import timezone
from django.db.utils import OperationalError, IntegrityError
from django.db import transaction # Для атомарных операций

# Импорт моделей. Убедитесь, что AUTH_USER_MODEL настроен на 'app_studio.CustomUser'
from app_studio.models import (
    CustomUser, Executor, OrderStatus, Service, CostCalculator, Order,
    Review, News, Message, Cart, CartItem, Portfolio, ExecutorService
)

# --- Функция для безопасного удаления ---
def safe_delete(model):
    print(f"Deleting data from {model.__name__}...")
    try:
        model.objects.all().delete()
        print(f"Successfully deleted data from {model.__name__}.")
    except OperationalError as e:
        print(f"Could not delete from {model.__name__} (table might not exist yet): {e}")
    except Exception as e:
        print(f"An error occurred while deleting from {model.__name__}: {e}")

# --- 1. Удаляем существующие данные в корректном порядке ---
print("--- Deleting existing data ---")
# Зависимые от Cart, Order, Review, Message, Portfolio, ExecutorService
safe_delete(CartItem)
safe_delete(Cart) # Удаляем корзины после их элементов
safe_delete(Order)
safe_delete(Review)
safe_delete(Message)
safe_delete(Portfolio)
safe_delete(ExecutorService)
# Зависимые от Service, Executor, OrderStatus
safe_delete(CostCalculator)
safe_delete(Service)
safe_delete(Executor)
safe_delete(OrderStatus)
# Зависимые от CustomUser
safe_delete(News) # Зависит от CustomUser (author)
safe_delete(CustomUser) # Удаляем пользователей последними перед OrderStatus (если не считать OrderStatus -> Order)
# Статусы можно не удалять каждый раз, если они фиксированы, но для чистоты удалим
# safe_delete(OrderStatus) # Перенесли выше

print("--- Data deletion phase complete ---")

# --- Обертка в транзакцию для атомарности ---
try:
    with transaction.atomic():
        print("--- Starting data population within a transaction ---")

        # --- 2. Создаем статусы заказов (OrderStatus) ---
        print("Creating OrderStatus...")
        status_data = [
            ('new', 'Новый'),
            ('processing', 'В обработке'),
            ('completed', 'Выполнен'),
            ('cancelled', 'Отменён'),
        ]
        order_statuses = {}
        for code, display in status_data:
            # Используем get_or_create, чтобы избежать ошибок при повторном запуске скрипта
            # и чтобы не зависеть от автоинкрементного ID
            status, created = OrderStatus.objects.get_or_create(
                status_name=code,
                # defaults можно не указывать, т.к. status_name уникально
            )
            order_statuses[code] = status
            if created:
                print(f"  Created OrderStatus: {display}")
            else:
                print(f"  Found OrderStatus: {display}")
        print("OrderStatus creation complete.")

        # --- 3. Создаем пользователей (CustomUser) ---
        print("Creating CustomUser...")
        user_data = [
            {"username": "AlexClient", "first_name": "Алексей", "last_name": "Петров", "phone_number": "+79161234567", "email": "alex@example.com", "password": "passComplex123!"},
            {"username": "MariaClient", "first_name": "Мария", "last_name": "Иванова", "phone_number": "+79267654321", "email": "maria@example.com", "password": "mariaPassSecure1"},
            {"username": "JohnExecutor", "first_name": "Иван", "last_name": "Сидоров", "phone_number": "+79031112233", "email": "john@example.com", "password": "johnSecurePass2024"},
            {"username": "KateExecutor", "first_name": "Екатерина", "last_name": "Смирнова", "phone_number": "+79854455667", "email": "kate@example.com", "password": "kateSuperPass456"},
            {"username": "MikeExecutor", "first_name": "Михаил", "last_name": "Кузнецов", "phone_number": "+79159988776", "email": "mike@example.com", "password": "mikeStrongPwd789"},
            {"username": "OlgaClient", "first_name": "Ольга", "last_name": "Васильева", "phone_number": "+79253334455", "email": "olga@example.com", "password": "olgaSecretCode1"},
            {"username": "RobertAdmin", "first_name": "Роберт", "last_name": "Попов", "phone_number": "+79657778899", "email": "robert@example.com", "password": "robAdminP@ss5", "is_staff": True, "is_superuser": True}, # Администратор
            {"username": "LauraClient", "first_name": "Лаура", "last_name": "Новикова", "phone_number": "+79291010101", "email": "laura@example.com", "password": "lauraUserPwd2"},
            {"username": "SteveExecutor", "first_name": "Степан", "last_name": "Морозов", "phone_number": "+79102030405", "email": "steve@example.com", "password": "steveExecXYZ9"},
            {"username": "EmilyClient", "first_name": "Эмилия", "last_name": "Лебедева", "phone_number": "+79995050607", "email": "emily@example.com", "password": "emilyClient2024"},
        ]
        users = []
        for data in user_data:
            user, created = CustomUser.objects.get_or_create(
                username=data["username"],
                defaults={
                    "first_name": data.get("first_name", ""),
                    "last_name": data.get("last_name", ""),
                    "phone_number": data["phone_number"],
                    "email": data["email"],
                    "is_staff": data.get("is_staff", False),
                    "is_superuser": data.get("is_superuser", False),
                    "date_joined": timezone.now() - timedelta(days=random.randint(10, 300))
                }
            )
            if created:
                user.set_password(data["password"])
                user.save()
                print(f"  Created User: {user.username}")
            else:
                print(f"  Found User: {user.username}")
            users.append(user)
        admin_user = CustomUser.objects.get(username="RobertAdmin") # Найдем админа для новостей
        print("CustomUser creation complete.")

        # --- 4. Создаем исполнителей (Executor) из некоторых пользователей ---
        print("Creating Executor...")
        executors_map = {} # Словарь для быстрого доступа user -> executor
        executors = []
        executor_users = [u for u in users if "Executor" in u.username] # Выбираем пользователей-исполнителей
        specializations = ["Видеомонтаж", "Цветокоррекция", "Съемка", "Графика 2D", "Графика 3D", "Аэросъемка", "Режиссура"]
        for user in executor_users:
            executor, created = Executor.objects.get_or_create(
                user=user,
                defaults={
                    "specialization": random.choice(specializations),
                    "experience_years": random.randint(1, 15),
                    "portfolio_link": f"https://portfolio.example.com/{user.username.lower()}",
                    "created_at": user.date_joined + timedelta(days=random.randint(1, 5)) # Профиль создан чуть позже регистрации
                }
            )
            if created:
                print(f"  Created Executor: {executor}")
            else:
                print(f"  Found Executor: {executor}")
            executors.append(executor)
            executors_map[user.id] = executor
        print("Executor creation complete.")

        # --- 5. Создаем услуги (Service) и калькуляторы стоимости (CostCalculator) ---
        print("Creating Service and CostCalculator...")
        services_data = [
            {"name": "Базовый видеомонтаж", "price": 15000, "desc": "Монтаж до 5 мин, базовая цветокоррекция, простые титры.", "hours": 8},
            {"name": "Продвинутый видеомонтаж", "price": 35000, "desc": "Монтаж до 15 мин, детальная цветокоррекция, эффекты, графика.", "hours": 24},
            {"name": "Цветокоррекция видео", "price": 10000, "desc": "Профессиональная цветокоррекция видеоматериала (до 10 мин).", "hours": 6},
            {"name": "Создание 2D анимации", "price": 25000, "desc": "Разработка и анимация 2D персонажей/сцен (за 1 мин).", "hours": 30},
            {"name": "Создание 3D модели", "price": 40000, "desc": "Моделирование и текстурирование 3D объекта (средняя сложность).", "hours": 40},
            {"name": "3D Анимация", "price": 50000, "desc": "Анимация 3D сцены или персонажа (за 30 сек).", "hours": 50},
            {"name": "Видеосъемка мероприятия", "price": 25000, "desc": "Репортажная съемка (до 4 часов работы оператора).", "hours": 4},
            {"name": "Аэросъемка", "price": 18000, "desc": "Съемка с дрона (1 вылет, до 1 часа в локации).", "hours": 2},
            {"name": "Режиссура рекламного ролика", "price": 30000, "desc": "Разработка концепции, сценария, руководство съемками.", "hours": 16},
            {"name": "Создание рекламного видео 'под ключ'", "price": 100000, "desc": "Полный цикл: идея, съемка, монтаж, графика, звук.", "hours": 80},
        ]
        services = []
        for s_data in services_data:
            service, created = Service.objects.get_or_create(
                name=s_data["name"],
                defaults={
                    "description": s_data["desc"],
                    "price": s_data["price"],
                    "duration_hours": s_data["hours"],
                    "created_at": timezone.now() - timedelta(days=random.randint(5, 100))
                }
            )
            if created:
                print(f"  Created Service: {service.name}")
                # Создаем калькулятор только для новых услуг
                additional = round(random.uniform(0, service.price * 0.2), 2) # Доп стоимость до 20% от базовой
                CostCalculator.objects.create(
                    service=service,
                    base_price=service.price,
                    additional_cost=additional,
                    # total_cost рассчитывается в методе save модели
                    updated_at=service.created_at + timedelta(microseconds=1) # Чуть позже создания услуги
                )
                print(f"    Created CostCalculator for {service.name}")
            else:
                print(f"  Found Service: {service.name}")
                # Проверяем, есть ли калькулятор, и создаем, если нет
                if not hasattr(service, 'cost_calculator'):
                     additional = round(random.uniform(0, service.price * 0.2), 2)
                     CostCalculator.objects.create(
                         service=service,
                         base_price=service.price,
                         additional_cost=additional,
                         updated_at=timezone.now()
                     )
                     print(f"    Created missing CostCalculator for {service.name}")

            services.append(service)
        print("Service and CostCalculator creation complete.")

        # --- 6. Создаем связи Исполнитель-Услуга (ExecutorService) ---
        print("Creating ExecutorService...")
        if services and executors:
            for executor in executors:
                # Каждый исполнитель оказывает от 1 до 4 случайных услуг
                num_services = random.randint(1, min(4, len(services)))
                executor_services_sample = random.sample(services, num_services)
                for service in executor_services_sample:
                    # 10% шанс установить кастомную цену (чуть выше или ниже базовой)
                    custom_p = None
                    if random.random() < 0.1:
                        custom_p = round(service.price * random.uniform(0.9, 1.15), 2)

                    es, created = ExecutorService.objects.get_or_create(
                        executor=executor,
                        service=service,
                        defaults={'custom_price': custom_p}
                    )
                    if created:
                         print(f"  Linked {executor.user.username} to {service.name}" + (f" (Custom Price: {custom_p})" if custom_p else ""))
        else:
             print("  Skipping ExecutorService creation (no services or executors found).")
        print("ExecutorService creation complete.")

        # --- 7. Создаем заказы (Order) ---
        print("Creating Order...")
        clients = [u for u in users if not hasattr(u, 'executor_profile')] # Пользователи без профиля исполнителя
        if clients and executors and services and order_statuses:
            for i in range(15): # Создадим 15 заказов
                client = random.choice(clients)
                # Выбираем исполнителя, который МОЖЕТ выполнить нужную услугу
                possible_executors = []
                while not possible_executors:
                    service = random.choice(services)
                    # Находим исполнителей для этой услуги через ExecutorService
                    possible_executors = Executor.objects.filter(services=service) # Используем related_name='executors' из Service
                    if not possible_executors:
                        print(f"  Warning: No executors found for service '{service.name}'. Skipping order attempt for this service.")
                        service = None # Попробуем другую услугу в след. итерации
                        break # Выходим из while, если для услуги нет исполнителей

                if not service: continue # Если не нашли услугу с исполнителями, пропускаем итерацию

                executor = random.choice(possible_executors)
                status_code = random.choice(['new', 'processing', 'completed', 'cancelled'])
                status = order_statuses[status_code]
                created_time = timezone.now() - timedelta(days=random.randint(1, 150))
                scheduled_time = created_time + timedelta(days=random.randint(3, 30), hours=random.randint(1,12))
                completed_time = None
                if status.status_name == 'completed':
                    # Завершенные заказы должны были быть выполнены раньше текущего момента
                    # и позже запланированного (или около того)
                     completion_delay = timedelta(days=random.randint(-2, 5)) # Может быть завершен чуть раньше или позже
                     # Убедимся, что время завершения не в будущем
                     potential_completed_time = scheduled_time + completion_delay
                     if potential_completed_time < timezone.now():
                         completed_time = potential_completed_time
                     else:
                         # Если расчетное время в будущем, ставим завершение незадолго до сейчас
                         completed_time = timezone.now() - timedelta(hours=random.randint(1, 24))
                         # Убедимся, что оно позже времени создания
                         if completed_time < created_time:
                             completed_time = created_time + timedelta(minutes=30)


                Order.objects.create(
                    client=client,
                    executor=executor,
                    service=service,
                    status=status,
                    created_at=created_time,
                    scheduled_at=scheduled_time,
                    completed_at=completed_time
                )
            print(f"  Created 15 Orders.")
        else:
            print("  Skipping Order creation (missing clients, executors, services or statuses).")
        print("Order creation complete.")


        # --- 8. Создаем отзывы (Review) ---
        print("Creating Review...")
        completed_orders = Order.objects.filter(status__status_name='completed').select_related('client', 'executor')
        reviews_data = [
            {"rating": 5, "comment": "Превосходный монтаж! Все пожелания учтены, результат превзошел ожидания."},
            {"rating": 4, "comment": "Хорошая работа по цветокоррекции, но финальный рендер занял чуть больше времени."},
            {"rating": 5, "comment": "Анимация просто супер! Очень креативно и качественно."},
            {"rating": 4, "comment": "3D модель сделана хорошо, но были небольшие правки по текстурам."},
            {"rating": 5, "comment": "Съемка прошла отлично, оператор настоящий профессионал."},
            {"rating": 5, "comment": "Аэросъемка добавила фильму эпичности! Качество на высоте."},
            {"rating": 4, "comment": "Режиссер предложил интересные идеи, но согласование затянулось."},
            {"rating": 5, "comment": "Рекламное видео получилось ярким и эффективным. Спасибо!"},
            {"rating": 3, "comment": "Монтаж в целом нормальный, но не хватило динамики в некоторых сценах."},
            {"rating": 4, "comment": "Цветокоррекция сделала картинку лучше, но ожидал немного другого стиля."},
        ]
        review_count = 0
        if completed_orders:
            for order in completed_orders:
                # Добавляем отзыв с вероятностью 70%
                if random.random() < 0.7:
                    rev_data = random.choice(reviews_data)
                    try:
                        Review.objects.create(
                            user=order.client, # Автор отзыва - клиент из заказа
                            executor=order.executor, # Объект отзыва - исполнитель из заказа
                            # order=order, # Если добавили связь с заказом в модели Review
                            rating=rev_data["rating"],
                            comment=rev_data["comment"],
                            created_at=order.completed_at + timedelta(days=random.randint(1, 5)) if order.completed_at else timezone.now() # Отзыв после завершения
                        )
                        review_count += 1
                    except IntegrityError:
                         # Пропускаем, если отзыв от этого юзера на этого исполнителя уже есть (из-за unique_together)
                         # Или если отзыв на этот заказ уже есть
                         print(f"  Skipping duplicate review for Order {order.pk} or User {order.client.pk} -> Executor {order.executor.pk}")
                    except Exception as e:
                         print(f"  Error creating review for Order {order.pk}: {e}")

            print(f"  Created {review_count} Reviews for completed orders.")
        else:
            print("  Skipping Review creation (no completed orders found).")
        print("Review creation complete.")

        # --- 9. Создаем новости (News) ---
        print("Creating News...")
        news_data = [
            {"title": "Новые техники видеомонтажа в 2024", "content": "Узнайте о последних трендах и инструментах, которые меняют индустрию."},
            {"title": "Глубокая цветокоррекция: от теории к практике", "content": "Наш ведущий специалист делится секретами создания идеальной картинки."},
            {"title": "Почему 2D анимация все еще актуальна?", "content": "Разбираем преимущества и сферы применения классической анимации."},
            {"title": "Фотореалистичная 3D визуализация: кейс студии", "content": "Как мы создавали 3D тур для крупного застройщика."},
            {"title": "Оборудование для профессиональной видеосъемки", "content": "Обзор камер, оптики и света, которые мы используем в работе."},
            {"title": "Аэросъемка: юридические аспекты и лучшие ракурсы", "content": "Что нужно знать перед заказом съемки с дрона."},
            {"title": "Роль режиссера в создании корпоративного фильма", "content": "Как режиссерский подход влияет на конечный результат."},
            {"title": "Тренды рекламных видео в социальных сетях", "content": "Как сделать ролик, который станет вирусным."},
            {"title": "Скидка 15% на все услуги в этом месяце!", "content": "Не упустите шанс заказать профессиональное видео по выгодной цене."},
            {"title": "Наша студия ищет талантливых монтажеров", "content": "Присоединяйтесь к нашей команде профессионалов. Подробности на сайте."},
        ]
        if users: # Нужны пользователи для поля author
            for news_item in news_data:
                News.objects.create(
                    title=news_item["title"],
                    content=news_item["content"],
                    published_at=timezone.now() - timedelta(days=random.randint(1, 60)),
                    author=admin_user # Пусть автором будет админ
                )
            print(f"  Created {len(news_data)} News items.")
        else:
            print("  Skipping News creation (no users found).")
        print("News creation complete.")

        # --- 10. Создаем сообщения (Message) ---
        print("Creating Message...")
        messages_data = [
            "Здравствуйте! Хотел бы уточнить стоимость видеомонтажа свадьбы.",
            "Добрый день! Интересует цветокоррекция короткометражного фильма. Какие сроки?",
            "Привет! Нужна 2D анимация для интро на YouTube канал. Сможете помочь?",
            "Уточните, пожалуйста, возможность создания 3D модели дома по чертежам.",
            "Добрый день. Требуется видеосъемка конференции на целый день. Ваши условия?",
            "Возможна ли аэросъемка земельного участка в Подмосковье?",
            "Ищу режиссера для музыкального клипа. Есть ли у вас опыт?",
            "Сколько будет стоить рекламный ролик для Instagram на 15 секунд?",
            "Подскажите, работаете ли вы с материалом, снятым на телефон?",
            "Можно ли заказать у вас только озвучку видео?",
        ]
        if len(users) >= 2:
            for content in messages_data:
                sender, receiver = random.sample(users, 2) # Выбираем двух случайных разных пользователей
                Message.objects.create(
                    sender=sender,
                    receiver=receiver,
                    content=content,
                    sent_at=timezone.now() - timedelta(hours=random.randint(1, 200)),
                    is_read=random.choice([True, False]) # Случайно помечаем как прочитанное
                )
            print(f"  Created {len(messages_data)} Messages.")
        else:
            print("  Skipping Message creation (need at least 2 users).")
        print("Message creation complete.")


        # --- 11. Создаем портфолио (Portfolio) ---
        print("Creating Portfolio...")
        if executors:
            portfolio_count = 0
            for i in range(15): # Создадим 15 работ в портфолио
                executor = random.choice(executors)
                Portfolio.objects.create(
                    executor=executor,
                    title=f"Проект '{random.choice(['Альфа', 'Бета', 'Гамма'])}' №{i+1}",
                    video_link=f"https://videos.example.com/portfolio_{executor.user.username}_{i+1}",
                    description=f"Демонстрация навыков в {executor.specialization}. Выполнено для клиента {random.choice(['А', 'Б', 'В'])}.",
                    uploaded_at=timezone.now() - timedelta(days=random.randint(5, 200))
                )
                portfolio_count += 1
            print(f"  Created {portfolio_count} Portfolio items.")
        else:
            print("  Skipping Portfolio creation (no executors found).")
        print("Portfolio creation complete.")

        # --- 12. Создаем корзины и элементы корзин (Cart, CartItem) ---
        print("Creating Cart and CartItem...")
        if users and services:
            cart_count = 0
            cart_item_count = 0
            for user in users:
                # Создаем корзину для каждого пользователя (если еще нет)
                cart, created = Cart.objects.get_or_create(user=user)
                if created:
                    cart_count += 1
                # С вероятностью 50% добавляем что-то в корзину
                if random.random() < 0.5:
                    num_items = random.randint(1, min(3, len(services))) # От 1 до 3 разных товаров
                    items_in_cart = random.sample(services, num_items)
                    for service in items_in_cart:
                        # Добавляем товар, если его еще нет в этой корзине
                        item, item_created = CartItem.objects.get_or_create(
                            cart=cart,
                            service=service,
                            defaults={'quantity': random.randint(1, 3)} # Случайное количество
                        )
                        if item_created:
                            cart_item_count += 1
                            # Обновим дату обновления корзины
                            cart.save() # Это обновит updated_at у корзины

            print(f"  Created/Found {cart_count} Carts.")
            print(f"  Created {cart_item_count} CartItems.")
        else:
            print("  Skipping Cart/CartItem creation (no users or services found).")
        print("Cart and CartItem creation complete.")

        print("--- Data population transaction committed successfully! ---")

except Exception as e:
    print(f"--- An error occurred during data population! Transaction rolled back. ---")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("--- Database population script finished ---")
