from django.contrib import admin
from .models import Empresa

@admin.register(Empresa)
class Empresa(admin.ModelAdmin):
    list_display = ['razao_social', 'cnpj', 'logradouro', 'numero', 'cep', 'bairro', 'municipio']
    exclude = ('usuario_criador',)
    
    def save_model(self, request, obj, form, change):
        obj.usuario_criador = request.user
        super().save_model(request, obj, form, change)
    

