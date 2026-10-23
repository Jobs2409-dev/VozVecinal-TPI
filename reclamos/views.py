# backend_python/reclamos/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, SAFE_METHODS
from django.db.models import Count
from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import AreaDependencia, Categoria, Estado, Rol, Reclamo
from .repositories import ReclamoRepository
from .services import ReclamoService
from .serializers import *
from .permissions import *


# Helper para auditoría de IP (Clase 8 - OWASP Logging & Monitoring)
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


# ==============================================================================
# CLASE 2 & 7: Catálogos del Sistema (Lectura Pública vs Escritura RBAC)
# Concepto: Métodos seguros (GET, HEAD, OPTIONS) mediante SAFE_METHODS permiten
# la lectura abierta con AllowAny, mientras que la modificación (POST, PUT, DELETE)
# exige estar autenticado y poseer el rol 'ADMIN'.
# ==============================================================================

class AreaDependenciaViewSet(viewsets.ModelViewSet):
    queryset = AreaDependencia.objects.all()
    serializer_class = AreaDependenciaSerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUserRole()]


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.select_related('area').all()
    serializer_class = CategoriaSerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUserRole()]


class EstadoViewSet(viewsets.ModelViewSet):
    queryset = Estado.objects.all()
    serializer_class = EstadoSerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUserRole()]


class RolViewSet(viewsets.ReadOnlyModelViewSet):
    """
    CLASE 7: Consulta de roles definidos para el control de acceso.
    """
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]


# ==============================================================================
# CLASE 6: Autenticación, Registro y Perfil
# Concepto: Gestión de credenciales, hashing de contraseñas y consulta
# del usuario autenticado (/me/).
# ==============================================================================

class AuthViewSet(viewsets.GenericViewSet):

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def seed_data(self, request):
        """
        CLASE 2 & 3: Inicialización de catálogos base del sistema.
        Garantiza la existencia de Roles, Estados iniciales y Categorías por defecto.
        """
        # 1. Roles del sistema (RBAC)
        for r in ['VECINO', 'OPERADOR', 'ADMIN']:
            Rol.objects.get_or_create(nombre=r)

        # 2. Estados del ciclo de vida del reclamo
        for e in ['Pendiente', 'En Proceso', 'Resuelto', 'Rechazado']:
            Estado.objects.get_or_create(nombre=e)

        # 3. Estructura inicial de Áreas y Categorías
        area, _ = AreaDependencia.objects.get_or_create(
            nombre="Obras y Servicios Públicos", 
            descripcion="Atención de infraestructura urbana"
        )
        Categoria.objects.get_or_create(nombre="Bacheo y Asfalto", area=area)
        Categoria.objects.get_or_create(nombre="Alumbrado Público", area=area)

        return Response({
            "status": "ok",
            "message": "Estructura de datos e inicialización de catálogos completada."
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        serializer = RegistroUsuarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UsuarioSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)


# ==============================================================================
# CLASES 2, 5, 7 & 8: ViewSet Principal de Reclamos y Endpoints Públicos
# Concepto: Aislamiento de lógica en capas (Service/Repository), filtrado por
# propietario (Owner) y exposición de datos abiertos anonimizados (AllowAny).
# ==============================================================================

class ReclamoViewSet(viewsets.ModelViewSet):
    # Definición de backends de filtrado, búsqueda y ordenamiento (clase 5)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado_actual', 'categoria', 'categoria__area']
    search_fields = ['titulo', 'descripcion']
    ordering_fields = ['fecha_creacion', 'id']
    ordering = ['-fecha_creacion']

    def get_permissions(self):
        if self.action in ['publicos', 'estadisticas']:
            return [AllowAny()]
        return [IsAuthenticated(), IsOwnerOrAdminOrOperator()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return ReclamoRepository.get_all_optimized().none()

        if user.rol and user.rol.nombre in ['OPERADOR', 'ADMIN']:
            return ReclamoRepository.get_all_optimized()

        return ReclamoRepository.get_by_user_optimized(user)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ReclamoCreateUpdateSerializer
        return ReclamoReadSerializer

    def perform_create(self, serializer):
        ip_address = get_client_ip(self.request)
        reclamo = ReclamoService.crear_reclamo(
            usuario=self.request.user,
            titulo=serializer.validated_data['titulo'],
            descripcion=serializer.validated_data['descripcion'],
            categoria_id=serializer.validated_data['categoria'].id,
            ip_address=ip_address
        )
        serializer.instance = reclamo

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsOperatorOrAdmin])
    def cambiar_estado(self, request, pk=None):
        serializer = CambiarEstadoReclamoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            reclamo_actualizado = ReclamoService.cambiar_estado(
                reclamo_id=pk,
                nuevo_estado_id=serializer.validated_data['nuevo_estado_id'],
                operador=request.user,
                observacion=serializer.validated_data['observacion'],
                ip_address=get_client_ip(request)
            )
            return Response(ReclamoReadSerializer(reclamo_actualizado).data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({'detail': e.message}, status=status.HTTP_400_BAD_REQUEST)

    # CLASE 2 & 5: Lectura pública anonimizada de reclamos (Sin Auth)
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def publicos(self, request):
        reclamos_publicos = ReclamoRepository.get_all_optimized()[:50]
        serializer = ReclamoReadSerializer(reclamos_publicos, many=True)
        
        # Ocultamiento de datos sensibles de la persona que realiza el reclamo
        data_anonima = serializer.data
        for item in data_anonima:
            if 'usuario' in item and item['usuario']:
                item['usuario'] = {
                    'username': item['usuario'].get('username', 'Vecino Anónimo')
                }
        
        return Response(data_anonima, status=status.HTTP_200_OK)

    # CLASE 2 & 5: Consulta pública de métricas globales (Sin Auth)
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def estadisticas(self, request):
        total_reclamos = Reclamo.objects.count()
        por_estado = Reclamo.objects.values('estado_actual__nombre').annotate(cantidad=Count('id'))
        
        return Response({
            'total_reclamos': total_reclamos,
            'por_estado': por_estado
        }, status=status.HTTP_200_OK)
        
        