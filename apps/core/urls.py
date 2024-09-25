from django.urls import path, include

from .views import InicioView

urlpatterns = [
    path('', InicioView.as_view(), name='inicio'),
]