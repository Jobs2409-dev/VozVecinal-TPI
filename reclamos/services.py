# backend_python/reclamos/services.py
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Reclamo, Estado, RegistroHistorial
from .repositories import ReclamoRepository, EstadoRepository, SecurityLogRepository

# ==============================================================================
# CLASE 3, 7 & 8: Capa de Servicios, Transacciones Atómicas y Auditoría
# Concepto: Lógica de negocio pura aislada de las vistas. Uso de transaction.atomic()
# para garantizar consistencia ACID al modificar el estado de un reclamo e historial.
# ==============================================================================

class ReclamoService:

    @staticmethod
    def crear_reclamo(usuario, titulo: str, descripcion: str, categoria_id: int, ip_address: str = None) -> Reclamo:
        """
        Crea un nuevo reclamo asignándole el estado inicial 'Pendiente'.
        """
        estado_inicial = EstadoRepository.get_by_nombre('Pendiente')
        if not estado_inicial:
            raise ValidationError("El estado inicial 'Pendiente' no existe en la base de datos.")

        with transaction.atomic():
            reclamo = Reclamo.objects.create(
                usuario=usuario,
                titulo=titulo,
                descripcion=descripcion,
                categoria_id=categoria_id,
                estado_actual=estado_inicial
            )
            
            # Historial de creación
            RegistroHistorial.objects.create(
                reclamo=reclamo,
                estado=estado_inicial,
                observacion="Reclamo ingresado en el sistema.",
                usuario_operador=None
            )

            # Auditoría OWASP (Clase 8)
            SecurityLogRepository.log_event(
                user=usuario,
                action="RECLAMO_CREADO",
                detail=f"Reclamo #{reclamo.id} creado.",
                ip_address=ip_address
            )

        return reclamo

    @staticmethod
    def cambiar_estado(reclamo_id: int, nuevo_estado_id: int, operador, observacion: str, ip_address: str = None) -> Reclamo:
        """
        Cambia el estado de un reclamo y registra la transición en el historial.
        """
        reclamo = ReclamoRepository.get_by_id_with_history(reclamo_id)
        if not reclamo:
            raise ValidationError("El reclamo especificado no existe.")

        nuevo_estado = Estado.objects.filter(id=nuevo_estado_id).first()
        if not nuevo_estado:
            raise ValidationError("El nuevo estado especificado no es válido.")

        if reclamo.estado_actual_id == nuevo_estado.id:
            raise ValidationError("El reclamo ya se encuentra en ese estado.")

        # Transacción ACID para asegurar consistencia
        with transaction.atomic():
            estado_anterior_nombre = reclamo.estado_actual.nombre
            reclamo.estado_actual = nuevo_estado
            reclamo.save()

            RegistroHistorial.objects.create(
                reclamo=reclamo,
                estado=nuevo_estado,
                observacion=observacion,
                usuario_operador=operador
            )

            SecurityLogRepository.log_event(
                user=operador,
                action="RECLAMO_CAMBIO_ESTADO",
                detail=f"Reclamo #{reclamo.id} pasó de {estado_anterior_nombre} a {nuevo_estado.nombre}.",
                ip_address=ip_address
            )

        return reclamo