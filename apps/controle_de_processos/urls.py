from django.urls import path
from .views import ProcessoCreate, ProcessoUpdate, ProcessoDelete, ProcessoList, ProcessoDetailView, LimparCacheProcessoView
from .views import AndamentoCreate, AndamentoUpdate, AndamentoDelete, AndamentoList, AndamentoDetailView
from .views import RelatoriosProcesso, RelatorioProcessosPorStatus, RelatorioAvaliacoes
from .views import LancamentoUsuario
from .views import BuscaDocumento, BuscaAndamentoPeloCodigo, BuscaPrazo, BuscaPagamento, BuscaEncaminhamento, BuscaNumeroAiti, BuscaAvaliacaoImobiliaria, VerificaMatricula, RelatorioGrafico
from . import views



urlpatterns = [
    # PROCESSO
    path('create/', ProcessoCreate.as_view(), name='processo-create'),
    path('busca-documento/', BuscaDocumento.as_view(), name='busca-documento'),
    path('detail-view/<int:id>/', ProcessoDetailView.as_view(), name='processo-detail-view'),
    path('update/<int:id>/', ProcessoUpdate.as_view(), name='processo-update'),
    path('delete/<int:id>/', ProcessoDelete.as_view(), name='processo-delete'),
    path('', ProcessoList.as_view(), name='processo-list'),
    path('limpar-cache/', LimparCacheProcessoView.as_view(), name='limpar-cache-processos'),
        
    # ANDAMENTO
    path('andamento/create/<int:id>/', AndamentoCreate.as_view(), name='andamento-create'),
    path('andamento/busca-codigo/', BuscaAndamentoPeloCodigo.as_view(), name='busca-codigo'),
    path('andamento/busca-prazo/', BuscaPrazo.as_view(), name='busca-prazo'),
    path('andamento/busca-pagamento/', BuscaPagamento.as_view(), name='busca-pagamento'),
    path('andamento/busca-encaminhamento/', BuscaEncaminhamento.as_view(), name='busca-encaminhamento'),
    path('andamento/busca-numero_aiti/', BuscaNumeroAiti.as_view(), name='busca-numero_aiti'),
    path('andamento/busca-avaliacao_imobiliaria/', BuscaAvaliacaoImobiliaria.as_view(), name='busca-avaliacao_imobiliaria'),
    path('andamento/verifica-matricula/', VerificaMatricula.as_view(), name='verifica-matricula'),
    path('andamento/detail-view/<int:id>/', AndamentoDetailView.as_view(), name='andamento-detail-view'),
    path('andamento/update/<int:id>/', AndamentoUpdate.as_view(), name='andamento-update'),
    path('andamento/delete/<int:id>/', AndamentoDelete.as_view(), name='andamento-delete'),
    path('andamento/list/<int:id>/', AndamentoList.as_view(), name='andamento-list'),

    # RELATÓRIOS 
    path('relatorios/', RelatoriosProcesso.as_view(), name='relatorios-processo' ),
    path('relatorio-processos-por-status/', RelatorioProcessosPorStatus.as_view(), name='processos-por-status'),
    path('relatorio-avaliacoes/', RelatorioAvaliacoes.as_view(), name='avaliacoes'),
    path('relatorio-grafico', RelatorioGrafico.as_view(), name='grafico'),

    # LANCAMENTOS POR USUARIO
    path('lancamentos-por-usuario/', LancamentoUsuario.as_view(), name='lancamento-por-usuario'),

]