from typing import Any, TYPE_CHECKING

from rest_framework import permissions
from rest_framework.request import Request 
from rest_framework.views import APIView 

if TYPE_CHECKING:
    from django.db.models import Model 
    from .models import CustomUser 

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешает чтение всем, а запись (изменение, удаление) только владельцу объекта.

    Предполагает, что у объекта (`obj`) есть поле, указывающее на владельца.
    По умолчанию это поле 'user', но может быть 'client' (для модели Order)
    или 'sender' (для модели Message).
    """
    def has_object_permission(self, request: Request, view: APIView, obj: 'Model') -> bool:
        """
        Проверяет, имеет ли запрашивающий пользователь права на объект.

        Args:
            request: Объект DRF Request.
            view: View, к которому применяется разрешение.
            obj: Объект модели, к которому запрашивается доступ.

        Returns:
            bool: True, если доступ разрешен, иначе False.
        """
        if request.method in permissions.SAFE_METHODS:
            return True

        owner_field_name: str = 'user'
        if hasattr(obj, 'client'):
            owner_field_name = 'client'
        elif hasattr(obj, 'sender'):
            owner_field_name = 'sender'

        current_user: Any = request.user
        return hasattr(obj, owner_field_name) and getattr(obj, owner_field_name) == current_user


class IsCartOwner(permissions.BasePermission):
    """
    Разрешает доступ к объекту корзины только ее владельцу.

    Предполагает, что у объекта корзины (`obj`) есть поле 'user',
    связанное с пользователем-владельцем.
    """
    def has_object_permission(self, request: Request, view: APIView, obj: 'Model') -> bool:
        """
        Проверяет, является ли запрашивающий пользователь владельцем корзины.

        Args:
            request: Объект DRF Request.
            view: View, к которому применяется разрешение.
            obj: Объект модели Cart.

        Returns:
            bool: True, если пользователь является владельцем корзины, иначе False.
        """
        current_user: Any = request.user
        return current_user and current_user.is_authenticated and hasattr(obj, 'user') and obj.user == current_user 

class IsMessageParticipantOrReadOnly(permissions.BasePermission):
    """
    Разрешает чтение сообщений всем аутентифицированным пользователям.
    Создание/изменение/удаление (если разрешено ViewSet'ом) доступно только
    участникам сообщения (отправителю или получателю).
    """
    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Проверяет общие права доступа к эндпоинту (на уровне ViewSet).
        Разрешает доступ, если пользователь аутентифицирован.

        Args:
            request: Объект DRF Request.
            view: View, к которому применяется разрешение.

        Returns:
            bool: True, если пользователь аутентифицирован, иначе False.
        """
        current_user: Any = request.user
        return bool(current_user and current_user.is_authenticated)

    def has_object_permission(self, request: Request, view: APIView, obj: 'Model') -> bool:
        """
        Проверяет права доступа к конкретному объекту сообщения.
        Для безопасных методов (GET, HEAD, OPTIONS) разрешает доступ аутентифицированным пользователям.
        Для других методов разрешает доступ только отправителю или получателю сообщения.

        Args:
            request: Объект DRF Request.
            view: View, к которому применяется разрешение.
            obj: Объект модели Message.

        Returns:
            bool: True, если доступ разрешен, иначе False.
        """
        current_user: Any = request.user
        if not (current_user and current_user.is_authenticated):
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return hasattr(obj, 'sender') and hasattr(obj, 'receiver') and \
               (obj.sender == current_user or obj.receiver == current_user) 

class IsAdminOrExecutorOrReadOnly(permissions.BasePermission):
    """
    Разрешает чтение (GET, HEAD, OPTIONS) всем пользователям.
    Разрешает запись (POST, PUT, PATCH, DELETE) только администраторам (`is_staff`)
    или пользователям, у которых есть профиль исполнителя (`executor_profile`).
    """
    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Проверяет общие права доступа к эндпоинту.

        Args:
            request: Объект DRF Request.
            view: View, к которому применяется разрешение.

        Returns:
            bool: True, если доступ разрешен, иначе False.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        
        current_user: 'CustomUser' = request.user 
        return bool(
            current_user and
            current_user.is_authenticated and
            (current_user.is_staff or hasattr(current_user, 'executor_profile'))
        )

class IsPortfolioOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешает чтение всем пользователям.
    Разрешает редактирование/удаление только владельцу портфолио (исполнителю,
    чей `user` совпадает с `request.user`) или администратору (`is_staff`).
    """
    def has_object_permission(self, request: Request, view: APIView, obj: 'Model') -> bool:
        """
        Проверяет права доступа к конкретному объекту портфолио.

        Args:
            request: Объект DRF Request.
            view: View, к которому применяется разрешение.
            obj: Объект модели Portfolio.

        Returns:
            bool: True, если доступ разрешен, иначе False.
        """
        if request.method in permissions.SAFE_METHODS:
            return True

        current_user: 'CustomUser' = request.user 
        return bool(
            current_user and
            current_user.is_authenticated and
            (current_user.is_staff or (hasattr(obj, 'executor') and obj.executor and obj.executor.user == current_user)) 
        )

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешает чтение (GET, HEAD, OPTIONS) всем пользователям.
    Разрешает запись (POST, PUT, PATCH, DELETE) только администраторам (`is_staff`).
    """
    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Проверяет общие права доступа к эндпоинту.

        Args:
            request: Объект DRF Request.
            view: View, к которому применяется разрешение.

        Returns:
            bool: True, если доступ разрешен, иначе False.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        
        current_user: 'CustomUser' = request.user 
        return bool(current_user and current_user.is_authenticated and current_user.is_staff)