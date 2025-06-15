from typing import Optional, Any 
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.http import HttpRequest 
from .models import CustomUser

class EmailOrUsernameBackend(ModelBackend):
    """
    Кастомный бэкенд аутентификации, который позволяет пользователям
    входить в систему, используя либо их имя пользователя (username),
    либо адрес электронной почты (email).
    """
    def authenticate(self, request: Optional[HttpRequest], username: Optional[str] = None, password: Optional[str] = None, **kwargs: Any) -> Optional[CustomUser]:
        """
        Аутентифицирует пользователя.

        Пытается найти пользователя по `username` или `email` (регистронезависимо).
        Если пользователь найден, проверяет пароль.

        Args:
            request: Объект HttpRequest (может быть None).
            username: Имя пользователя или email для аутентификации.
            password: Пароль пользователя.
            **kwargs: Дополнительные именованные аргументы.

        Returns:
            Optional[CustomUser]: Объект пользователя, если аутентификация прошла успешно, иначе None.
        """
        if not username or not password:
            return None
        try:
            user: CustomUser = CustomUser.objects.get(Q(username=username) | Q(email__iexact=username))
        except CustomUser.DoesNotExist:
            return None
        except CustomUser.MultipleObjectsReturned:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id: int) -> Optional[CustomUser]:
        """
        Возвращает объект пользователя по его ID.

        Используется Django для загрузки пользователя в сессию.

        Args:
            user_id: Первичный ключ (ID) пользователя.

        Returns:
            Optional[CustomUser]: Объект пользователя, если найден, иначе None.
        """
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None