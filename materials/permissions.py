from rest_framework import permissions


class IsModerator(permissions.BasePermission):
    """
    Права доступа для модераторов
    Модераторы могут просматривать и редактировать любые объекты, но не могут создавать и удалять
    """

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.groups.filter(name='moderators').exists()
        return False

    def has_object_permission(self, request, view, obj):
        # Модераторы могут просматривать и редактировать любые объекты
        return request.method in permissions.SAFE_METHODS or request.method in ['PUT', 'PATCH']


class IsOwnerOrModerator(permissions.BasePermission):
    """
    Владелец объекта может делать все, модератор - только читать и редактировать
    """

    def has_permission(self, request, view):
        # Для создания объектов - только не модераторы
        # Проверяем наличие атрибута action (есть в ViewSet) или используем метод запроса
        if hasattr(view, 'action'):
            if view.action == 'create':
                return request.user.is_authenticated and not request.user.groups.filter(name='moderators').exists()
        elif request.method == 'POST':
            # Для обычных APIView проверяем метод
            return request.user.is_authenticated and not request.user.groups.filter(name='moderators').exists()

        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Проверяем, является ли пользователь владельцем
        if hasattr(obj, 'owner') and obj.owner == request.user:
            return True

        # Проверяем, является ли пользователь модератором
        if request.user.groups.filter(name='moderators').exists():
            return request.method in permissions.SAFE_METHODS or request.method in ['PUT', 'PATCH']

        return False


class IsOwner(permissions.BasePermission):
    """
    Только владелец объекта имеет доступ
    """

    def has_object_permission(self, request, view, obj):
        return hasattr(obj, 'owner') and obj.owner == request.user