# backend_python/VozVecinal/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

# ==============================================================================
# CLASE 1: Introducción a DRF y Entorno de Desarrollo
# Concepto: Uso de variables de entorno para aislar credenciales sensibles
# de producción (.env) respecto al control de versiones (Git).
# ==============================================================================
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG') == 'True'

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    
    'rest_framework', # DRF para APIs RESTful (clase 1 y 2)
    'django_filters', # Paginación y filtros (clase 5)
    'corsheaders', # Seguridad y CORS (CLASE 8)
    
    # Apps del dominio
    'reclamos',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'VozVecinal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'VozVecinal.wsgi.application'

# ==============================================================================
# CLASE 1: Conexión a Base de Datos Relacional (MySQL)
# Concepto: Configuración del backend de DB mediante variables de entorno
# y conector mysqlclient.
# ==============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '3306'),
    }
}


# ==============================================================================
# CLASE 6: Configuración Global de DRF y Autenticación Stateless con JWT
# Concepto: Define SimpleJWT como esquema de autenticación por defecto y
# establece que los endpoints requieren estar autenticados por defecto.
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # Paginación estándar de 10 elementos por página y motores de filtro (clase 5)
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=630),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'es-ar'  # Configurado para localización local
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

# Email configuration
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}

# ==============================================================================
# CLASE 6 & 7: Modelos de Usuario Personalizados y Control de Acceso (RBAC)
# Concepto: Sobrescribir el modelo de usuario predeterminado de Django antes
# de ejecutar la primera migración para permitir la extensión de roles y perfil.
# ==============================================================================
AUTH_USER_MODEL = 'reclamos.Usuario'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# CLASE 8: Configuración de Orígenes Permitidos (CORS)
# Concepto: Permitir peticiones cross-origin desde entornos de desarrollo/frontend.
# ==============================================================================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",  # Vite/React default
]

# Para desarrollo local completo se puede habilitar temporalmente:
CORS_ALLOW_ALL_ORIGINS = True