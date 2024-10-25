from django.urls import path
from .views import FichaList, FichaCreate, LimpaCacheFichas, FichaUpdate, FichaDelete, Relatorios, GerarRelatorioGrafico

urlpatterns = [
    path('ficha/create/', FichaCreate.as_view(), name='ficha-create'),
    path('ficha/list/', FichaList.as_view(), name='ficha-list'),
    path('ficha/clean/', LimpaCacheFichas.as_view(), name='ficha-clean'),
    path('ficha/update/<int:pk>/', FichaUpdate.as_view(), name='ficha-update'),
    path('ficha/delete/<int:pk>/', FichaDelete.as_view(), name='ficha-delete'),
    path('ficha/relatorios/', Relatorios.as_view(), name='relatorios'),
    path('relatorio-grafico/', GerarRelatorioGrafico.as_view(), name='relatorio-grafico')
]