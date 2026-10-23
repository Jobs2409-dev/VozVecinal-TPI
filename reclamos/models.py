# backend_python/reclamos/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# ==============================================================================
# CLASE 7: Control de Acceso Basado en Roles (RBAC - Role-Based Access Control)
# Concepto: Definición de roles explícitos para gestionar los permisos dentro
# del sistema (Vecino, Operador, Administrador).
# ==============================================================================
class Rol(models.Model):
    NOMBRE_ROLES = (
        ('VECINO', 'Vecino'),
        ('OPERADOR', 'Operador'),
        ('ADMIN', 'Administrador'),
    )
    nombre = models.CharField(max_length=20, choices=NOMBRE_ROLES, unique=True)
    
    def __str__(self):
        return self.get_nombre_display()


# ==============================================================================
# CLASE 6: Autenticación, Usuarios y Perfiles
# Concepto: Extensión del modelo AbstractUser para centralizar las credenciales,
# asociar el Rol de acceso y agregar datos de contacto/identificación (DNI, Teléfono).
# ==============================================================================
class Usuario(AbstractUser):
    rol = models.ForeignKey(Rol, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    dni = models.CharField(max_length=15, blank=True, null=True, unique=True)

    def __str__(self):
        return f"{self.username} ({self.rol.nombre if self.rol else 'Sin Rol'})"


# ==============================================================================
# CLASE 2: Modelado del Dominio y Relaciones
# Concepto: Entidad que agrupa las dependencias municipales que atienden
# los distintos tipos de reclamos.
# ==============================================================================
class AreaDependencia(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre


# ==============================================================================
# CLASE 2 & 5: Clasificación de Datos y Optimización de Consultas
# Concepto: Categorización pública vinculada a un área. Permite luego aplicar
# select_related/prefetch_related en repositorios para evitar el problema N+1.
# ==============================================================================
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    area = models.ForeignKey(AreaDependencia, on_delete=models.CASCADE, related_name='categorias')

    def __str__(self):
        return f"{self.nombre} ({self.area.nombre})"


# ==============================================================================
# CLASE 3: Transiciones de Estado en Entidades de Negocio
# Concepto: Representa los estados del ciclo de vida del reclamo (ej: Pendiente,
# En Proceso, Resuelto, Rechazado).
# ==============================================================================
class Estado(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre


# ==============================================================================
# CLASE 2, 3 & 5: Entidad Principal de Negocio y Permisos por Propietario
# Concepto: Entidad central del sistema. Implementa relaciones FK con protección
# para evitar borrados en cascada no deseados (on_delete=models.PROTECT en Estado)
# y permite la filtración por dueño (get_queryset) vista en la Clase 6.
# ==============================================================================
class Reclamo(models.Model):
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reclamos')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='reclamos')
    estado_actual = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name='reclamos')

    def __str__(self):
        return f"Reclamo #{self.id}: {self.titulo} [{self.estado_actual.nombre}]"


# ==============================================================================
# CLASE 3 & 7: Trazabilidad, Historial y Operaciones Atómicas
# Concepto: Registro del historial de cambios de estado. Se utiliza en conjunto
# con transaction.atomic() en la capa de servicios (services.py) para garantizar
# que cada actualización de Reclamo cree obligatoriamente su registro histórico.
# ==============================================================================
class RegistroHistorial(models.Model):
    reclamo = models.ForeignKey(Reclamo, on_delete=models.CASCADE, related_name='registros')
    estado = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name='registros')
    observacion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    usuario_operador = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='registros_realizados'
    )

    def __str__(self):
        return f"Historial Reclamo #{self.reclamo.id} -> {self.estado.nombre}"


# ==============================================================================
# CLASE 8: Auditoría y Registro de Eventos de Seguridad (OWASP Top 10)
# Concepto: Modelo para auditar acciones sensibles (logins fallidos, cambios
# de rol, modificaciones críticas) junto con la IP y el usuario, cumpliendo
# con el control de Logging & Monitoring de OWASP.
# ==============================================================================
class SecurityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=100)
    detail = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.action} ({self.ip_address})"