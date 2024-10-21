from django.urls import path
from .views import FichaList, FichaCreate

urlpatterns = [
    path('ficha/create/', FichaCreate.as_view(), name='ficha-create'),
    path('ficha/list/', FichaList.as_view(), name='ficha-list')
]