from django.urls import path
from .views import FichaCreate

urlpatterns = [
    path('ficha/create/', FichaCreate.as_view(), name='ficha-create'),

    # path('grafico', Grafico.as_view(), name='grafico'),
]