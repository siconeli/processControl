from django.contrib import admin
from .models import TipoContato, TipoAtendimento, ClienteAtendimento, StatusAtendimento #CategoriaAtendimento

@admin.register(TipoContato)
class TipoContatoAdmin(admin.ModelAdmin):
    list_display = ['contato']

@admin.register(TipoAtendimento)
class TipoAtendimento(admin.ModelAdmin):
    list_display = ['atendimento', 'codigo']

@admin.register(ClienteAtendimento)
class ClienteAtendimentoAdmin(admin.ModelAdmin):
    list_display = ['nome_cliente']
    exclude = ['usuario_criador']

    def save_model(self, request, obj, form, change):
        obj.usuario_criador = request.user
        super().save_model(request, obj, form, change)

@admin.register(StatusAtendimento)
class StatusAtendimentoAdmin(admin.ModelAdmin):
    list_display = ['nome']
