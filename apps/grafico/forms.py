from django import forms
from .models import Ficha, ValorMes

class FichaForm(forms.ModelForm):
    class Meta:
        model = Ficha
        fields = ['municipio', 'receita', 'ano']

class ValorMesForm(forms.ModelForm):
    class Meta:
        model = ValorMes
        fields = ['janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']