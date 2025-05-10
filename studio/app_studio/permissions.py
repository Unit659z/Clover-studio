from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешает чтение всем, а запись (изменение, удаление) только владельцу объекта.
    Требует, чтобы у объекта было поле 'user' (или 'author', 'owner').
    """
    def has_object_permission(self, request, view, obj):
        # Разрешаем GET, HEAD, OPTIONS запросы всем
        if request.method in permissions.SAFE_METHODS:
            return True
        owner_field = 'user' # По умолчанию
        if hasattr(obj, 'client'): # Для Order
            owner_field = 'client'
        elif hasattr(obj, 'sender'): # Для Message
             owner_field = 'sender'

        #  поле существует и сравниваем
        return hasattr(obj, owner_field) and getattr(obj, owner_field) == request.user


class IsCartOwner(permissions.BasePermission):
    """
    Разрешает доступ только владельцу корзины.
    Объект (корзина) должен иметь поле 'user'.
    """
    def has_object_permission(self, request, view, obj):
        # Проверяем, что пользователь аутентифицирован и является владельцем корзины
        return request.user and request.user.is_authenticated and obj.user == request.user

class IsMessageParticipantOrReadOnly(permissions.BasePermission):
    """
    Разрешает чтение всем аутентифицированным пользователям,
    а создание/изменение/удаление (если разрешено) только участникам (отправителю или получателю).
    """
    def has_permission(self, request, view):
         # Чтение списка доступно всем аутентифицированным
         # Создание доступно всем аутентифицированным (проверка на self-send в сериализаторе)
         return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Разрешаем GET, HEAD, OPTIONS аутентифицированным пользователям
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Проверяем, является ли пользователь отправителем или получателем
        return request.user and request.user.is_authenticated and (obj.sender == request.user or obj.receiver == request.user)

class IsAdminOrExecutorOrReadOnly(permissions.BasePermission):
    """
    Разрешает чтение всем (GET, HEAD, OPTIONS).
    Разрешает запись (POST, PUT, PATCH, DELETE) только админам (is_staff)
    или пользователям, у которых есть профиль исполнителя.
    """
    def has_permission(self, request, view):
        # Разрешаем безопасные методы всем
        if request.method in permissions.SAFE_METHODS:
            return True
        # Для остальных методов проверяем аутентификацию и права
        return request.user and request.user.is_authenticated and \
               (request.user.is_staff or hasattr(request.user, 'executor_profile'))

class IsPortfolioOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешает чтение всем.
    Разрешает редактирование/удаление только владельцу портфолио (исполнителю)
    или администратору.
    """
    def has_object_permission(self, request, view, obj):
        # Разрешаем GET, HEAD, OPTIONS всем
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешаем запись владельцу или админу
        # У объекта Portfolio есть поле 'executor', у которого есть поле 'user'
        return request.user and request.user.is_authenticated and \
               (request.user.is_staff or (obj.executor and obj.executor.user == request.user))

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешает чтение всем (GET, HEAD, OPTIONS).
    Разрешает запись (POST, PUT, PATCH, DELETE) только админам (is_staff).
    """
    def has_permission(self, request, view):
        # Разрешаем безопасные методы всем
        if request.method in permissions.SAFE_METHODS:
            return True
        # Для остальных методов проверяем аутентификацию и права админа
        return request.user and request.user.is_authenticated and request.user.is_staff