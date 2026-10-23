# backend_python/reclamos/repositories.py
from typing import Optional
from django.db.models import QuerySet
from .models import Reclamo, Categoria, Estado, RegistroHistorial, AreaDependencia, SecurityLog

# ==============================================================================
# CLASE 5: Capa de Repositorios y Optimización de Consultas ORM
# Concepto: Abstracción de las consultas a la base de datos.
# Se aplican select_related y prefetch_related para evitar el problema N+1.
# ==============================================================================

class ReclamoRepository:

    @staticmethod
    def get_all_optimized() -> QuerySet[Reclamo]:
        """
        Retorna todos los reclamos optimizando las FKs con select_related.
        """
        return Reclamo.objects.select_related(
            'usuario', 
            'categoria', 
            'categoria__area', 
            'estado_actual'
        ).all().order_by('-fecha_creacion')

    @staticmethod
    def get_by_user_optimized(user) -> QuerySet[Reclamo]:
        """
        Retorna los reclamos pertenecientes a un usuario específico (Propietario).
        """
        return ReclamoRepository.get_all_optimized().filter(usuario=user)

    @staticmethod
    def get_by_id_with_history(reclamo_id: int) -> Optional[Reclamo]:
        """
        Obtiene un reclamo con su historial pre-cargado (prefetch_related).
        """
        return Reclamo.objects.select_related(
            'usuario', 
            'categoria', 
            'categoria__area', 
            'estado_actual'
        ).prefetch_related('registros__usuario_operador', 'registros__estado').filter(id=reclamo_id).first()


class EstadoRepository:

    @staticmethod
    def get_by_nombre(nombre: str) -> Optional[Estado]:
        return Estado.objects.filter(nombre__iexact=nombre).first()


class SecurityLogRepository:

    @staticmethod
    def log_event(user, action: str, detail: str = "", ip_address: str = None) -> SecurityLog:
        """
        Persiste un evento de auditoría de seguridad.
        """
        return SecurityLog.objects.create(
            user=user if user and user.is_authenticated else None,
            action=action,
            detail=detail,
            ip_address=ip_address
        )
        
        