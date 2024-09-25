from django.urls import path
from .views import AtendimentoCreate, AtendimentoList, LimparCacheView, AtendimentoDelete, AtendimentoUpdate
from . import views

urlpatterns = [
    path('atendimento/create/', AtendimentoCreate.as_view(), name='atendimento-create'),
    path('atendimento/list/', AtendimentoList.as_view(), name='atendimento-list'),
    path('atendimento/delete/<int:id>/', AtendimentoDelete.as_view(), name='atendimento-delete'),
    path('atendimento/update/<int:id>/', AtendimentoUpdate.as_view(), name='atendimento-update'),
    path('busca-processo/', views.filtrarProcessos, name='filtrar-processos'),
    path('atendimento/cadastrar-cliente/', views.ClienteAtendimentoCreate, name='cadastrar-cliente-atendimento'),
    path('atendimento/listar-cliente/', views.ListaDeClientes, name='listar-cliente-atendimento'),
    path('atendimento/buscar-tipo-atendimento/', views.BuscarTipoAtendimento, name='buscar-tipo-atendimento'),

    # Relatório
    path('relatorio-atendimentos/', views.relatorioAtendimentos, name='relatorio-atendimentos'),
    path('limpar-cache/', LimparCacheView.as_view(), name='limpar_cache'),
]
