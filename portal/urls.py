from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('central-admin/', admin.site.urls),
    path('inicio/', include('apps.core.urls')),
    path('empresa/', include('apps.empresa.urls')),
    path('funcionario/', include('apps.funcionarios.urls')),
    path('', include('apps.controle_de_processos.urls')),
    path('municipio/', include('apps.municipios.urls')),
    path('registro/', include('apps.registro.urls')),
    path('grafico/', include('apps.grafico.urls')),
    path('accounts/', include('django.contrib.auth.urls')), 
] 

if settings.DEBUG: 
    urlpatterns += static (settings.MEDIA_URL, document_root = settings.MEDIA_ROOT) 
    urlpatterns += static (settings.STATIC_URL, document_root = settings.STATIC_URL)

admin.site.site_title = 'Cadastros' 
admin.site.site_header = 'Central Administrativa' 
admin.site.index_title = 'Cadastros'