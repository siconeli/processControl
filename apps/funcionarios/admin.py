from django.contrib import admin
from .models import Funcionario, Departamento

@admin.register(Funcionario)
class Funcionario(admin.ModelAdmin):
    list_display = ['user', 'nome', 'empresa', 'departamento', 'assinatura']
    exclude = ('usuario_criador', 'origem')
    
    def save_model(self, request, obj, form, change):
        obj.usuario_criador = request.user
        super().save_model(request, obj, form, change)

@admin.register(Departamento)
class Departamento(admin.ModelAdmin):
    list_display = ['departamento']
    exclude = ('usuario_criador', )

    def save_model(self, request, obj, form, change):
        obj.usuario_criador = request.user
        super().save_model(request, obj, form, change)