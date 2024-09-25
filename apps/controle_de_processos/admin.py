from django.contrib import admin
from .models import TipoProcesso, TipoAndamentoAvaliacao, TipoAndamento, LocalizacaoProcesso, TipoOperacao, TipoFinalidade

@admin.register(TipoProcesso)
class TipoProcessoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'ativo')
    exclude = ['usuario_criador', 'origem']

    def save_model(self, request, obj, form, change):
        obj.usuario_criador = request.user
        super().save_model(request, obj, form, change)

@admin.register(TipoAndamento)
class TipoAndamentoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'tipo_andamento', 'status', 'prazo', 'pagamento', 'encaminhamento', 'numero_aiti', 'avaliacao_imobiliaria', 'criar_atendimento', 'ativo') 
    exclude = ['usuario_criador', 'origem']

    def save_model(self, request, obj, form, change):
        obj.usuario_criador = request.user
        super().save_model(request, obj, form, change)

@admin.register(TipoAndamentoAvaliacao)
class TipoAndamentoAvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('tipo_and_aval',)
    exclude = ['usuario_criador', 'origem']

    def save_model(self, request, obj, form, change):
        obj.usuario_criador = request.user
        super().save_model(request, obj, form, change)

@admin.register(LocalizacaoProcesso)
class LocalizacaoProcessoAdmin(admin.ModelAdmin):
    list_display = ('localizacao',)

@admin.register(TipoOperacao)
class TipoOperacaoAdmin(admin.ModelAdmin):
    list_display = ('tipo_ope_aval', 'calculo_operacao_aval')

@admin.register(TipoFinalidade)
class TipoFinalidadeAdmin(admin.ModelAdmin):
    list_display = ('tipo_finalidade',)