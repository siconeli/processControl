from django.contrib import admin
from .models import AnoFicha

@admin.register(AnoFicha)
class AnoFichaAdmin(admin.ModelAdmin):
    list_display = ("nome_ano", )
    exclude = ['usuario_criador', 'origem']
