# backend_python/reclamos/admin.py
from django.contrib import admin
from .models import *

admin.site.register(Usuario) # 1
admin.site.register(Reclamo) # 2
admin.site.register(Estado) # 3
admin.site.register(Categoria) # 4
admin.site.register(AreaDependencia) # 5
admin.site.register(Rol) # 6
admin.site.register(RegistroHistorial) # 7
admin.site.register(SecurityLog) # 8


# jo / 1234