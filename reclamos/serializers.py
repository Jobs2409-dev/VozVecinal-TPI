# backend_python/reclamos/serializers.py
import nh3 # Santización de entradas contra Cross-Site Scripting (XSS)
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Reclamo, Categoria, AreaDependencia, Estado, RegistroHistorial, Rol

User = get_user_model()


# ==============================================================================
# CLASE 6 & 7: Serializers para Autenticación y Usuarios (RBAC)
# Concepto: Registro seguro con hash de contraseña PBKDF2 y lectura de roles.
# ==============================================================================
class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id', 'nombre']


class UsuarioSerializer(serializers.ModelSerializer):
    rol = RolSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'dni', 'telefono', 'rol']


class RegistroUsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'dni', 'telefono']

    def create(self, validated_data):
        # Asigna el rol por defecto 'VECINO' si existe
        rol_vecino = Rol.objects.filter(nombre='VECINO').first()
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            dni=validated_data.get('dni'),
            telefono=validated_data.get('telefono'),
            rol=rol_vecino
        )
        return user


# ==============================================================================
# CLASE 2 & 5: Serializers para Auxiliares y Estructuras Anidadas
# Concepto: DTOs livianos para Categoria, Area y Estado.
# ==============================================================================
class AreaDependenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaDependencia
        fields = ['id', 'nombre', 'descripcion']


class CategoriaSerializer(serializers.ModelSerializer):
    area = AreaDependenciaSerializer(read_only=True)
    area_id = serializers.PrimaryKeyRelatedField(
        queryset=AreaDependencia.objects.all(),
        source='area',
        write_only=True
    )

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion', 'area', 'area_id']


class EstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estado
        fields = ['id', 'nombre']


class RegistroHistorialSerializer(serializers.ModelSerializer):
    estado = EstadoSerializer(read_only=True)
    usuario_operador = UsuarioSerializer(read_only=True)

    class Meta:
        model = RegistroHistorial
        fields = ['id', 'estado', 'observacion', 'fecha', 'usuario_operador']


# ==============================================================================
# CLASE 2, 5 & 6: Serializers Principales de Reclamo (Creación vs Lectura)
# Concepto: Validación defensiva con self.instance para soportes PATCH
# y separación entre payload de lectura (anidado) y escritura (IDs).
# ==============================================================================
class ReclamoReadSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    categoria = CategoriaSerializer(read_only=True)
    estado_actual = EstadoSerializer(read_only=True)
    registros = RegistroHistorialSerializer(many=True, read_only=True)

    class Meta:
        model = Reclamo
        fields = [
            'id', 'titulo', 'descripcion', 'fecha_creacion',
            'usuario', 'categoria', 'estado_actual', 'registros'
        ]


class ReclamoCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reclamo
        fields = ['titulo', 'descripcion', 'categoria']

    def validate_titulo(self, value):
        # Sanitización y validación de longitud
        cleaned_value = nh3.clean(value.strip())
        if len(cleaned_value) < 5:
            raise serializers.ValidationError("El título debe contener al menos 5 caracteres válidos.")
        return cleaned_value

    def validate_descripcion(self, value):
        # CLASE 8: Sanitización defensiva contra XSS eliminando etiquetas HTML/Script
        cleaned_value = nh3.clean(value.strip())
        if len(cleaned_value) < 10:
            raise serializers.ValidationError("La descripción debe contener al menos 10 caracteres válidos.")
        return cleaned_value


class CambiarEstadoReclamoSerializer(serializers.Serializer):
    nuevo_estado_id = serializers.IntegerField(required=True)
    observacion = serializers.CharField(required=True, min_length=5)