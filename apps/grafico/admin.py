from django.contrib import admin
from .models import Receita, Ano, Ficha, ValorMes

@admin.register(Receita)
class ReceitaAdmin(admin.ModelAdmin):
    list_display = ("nome", )

@admin.register(Ano)
class AnoAdmin(admin.ModelAdmin):
    list_display = ("nome", )

@admin.register(Ficha)
class FichaAdmin(admin.ModelAdmin):
    list_display = ("municipio", "receita", "ano")

@admin.register(ValorMes)
class ValorMesAdmin(admin.ModelAdmin):
    list_display = ("ficha", "janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro")