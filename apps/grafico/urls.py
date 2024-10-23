from django.urls import path
from .views import FichaList, FichaCreate, LimpaCacheFichas

urlpatterns = [
    path('ficha/create/', FichaCreate.as_view(), name='ficha-create'),
    path('ficha/list/', FichaList.as_view(), name='ficha-list'),
    path('ficha/clean/', LimpaCacheFichas.as_view(), name='ficha-clean')
]