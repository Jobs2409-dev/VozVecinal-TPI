# backend_python/reclamos/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import *

# ==============================================================================
# CLASE 2: Enrutado Automático con DRF Routers
# Concepto: DefaultRouter genera automáticamente las rutas RESTful estándar
# (GET, POST, PUT, PATCH, DELETE) para cada ViewSet registrado.
# ==============================================================================
router = DefaultRouter()
router.register(r'reclamos', ReclamoViewSet, basename='reclamo')
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'areas', AreaDependenciaViewSet, basename='area')
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'estados', EstadoViewSet, basename='estado')
router.register(r'roles', RolViewSet, basename='rol')

urlpatterns = [
    # CLASE 6: Autenticación Stateless con JWT
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Endpoints de los ViewSets
    path('', include(router.urls)),
]