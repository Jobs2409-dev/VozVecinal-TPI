# backend_python/reclamos/permissions.py
from rest_framework import permissions

# ==============================================================================
# CLASE 7: Permisos Personalizados Basados en Roles (RBAC)
# Concepto: Implementación de BasePermission para validar el rol almacenado
# en la entidad Usuario (Vecino, Operador, Administrador).
# ==============================================================================

class IsAdminUserRole(permissions.BasePermission):
    """
    Permite el acceso únicamente a usuarios con el rol 'ADMIN'.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.rol and 
            request.user.rol.nombre == 'ADMIN'
        )


class IsOperatorOrAdmin(permissions.BasePermission):
    """
    Permite el acceso a Operadores o Administradores para gestión de reclamos.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.rol and 
            request.user.rol.nombre in ['OPERADOR', 'ADMIN']
        )


class IsOwnerOrAdminOrOperator(permissions.BasePermission):
    """
    Garantiza que un Vecino solo acceda a su propio reclamo (Owner),
    mientras que los Operadores y Admins pueden ver cualquier reclamo.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Si es Operador o Admin, tiene acceso
        if request.user.rol and request.user.rol.nombre in ['OPERADOR', 'ADMIN']:
            return True

        # Si es Vecino, debe ser el propietario de la entidad
        return obj.usuario == request.user