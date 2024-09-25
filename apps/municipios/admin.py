from django.contrib import admin
from .models import Municipio

@admin.register(Municipio)
class Municipio(admin.ModelAdmin):
    list_display = ('nome', 'tipo_contrato', 'contrato', 'ativo', 'aliquota')
    exclude = ['usuario_criador']
    
    def save_model(self, request, obj, form, change):
        obj.usuario_criador = request.user
        super().save_model(request, obj, form, change)
