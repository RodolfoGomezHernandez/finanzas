from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('reportes.urls')),
    path('cuentas/', include('cuentas.urls')),
    path('categorias/', include('categorias.urls')),
    path('movimientos/', include('movimientos.urls')),
    path('creditos/', include('creditos.urls')),
]
