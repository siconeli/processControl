from django.db import models
from apps.core.models import Base
from apps.municipios.models import Municipio

class AnoFicha(models.Model):
    nome_ano = models.CharField(max_length=4)

    def __str__(self):
        return self.nome_ano

class Ficha(Base):
    municipio_fi = models.ForeignKey(Municipio, on_delete=models.CASCADE)
    ano_fi = models.ForeignKey(AnoFicha, on_delete=models.CASCADE)
    janeiro_fi = models.CharField(max_length=9)
    fevereiro_fi = models.CharField(max_length=9, blank=True, null=True)
    marco_fi = models.CharField(max_length=9, blank=True, null=True)
    abril_fi = models.CharField(max_length=9, blank=True, null=True)
    maio_fi = models.CharField(max_length=9, blank=True, null=True)
    junho_fi = models.CharField(max_length=9, blank=True, null=True)
    julho_fi = models.CharField(max_length=9, blank=True, null=True)
    agosto_fi = models.CharField(max_length=9, blank=True, null=True)
    setembro_fi = models.CharField(max_length=9, blank=True, null=True)
    outubro_fi = models.CharField(max_length=9, blank=True, null=True)
    novembro_fi = models.CharField(max_length=9, blank=True, null=True)
    dezembro_fi = models.CharField(max_length=9, blank=True, null=True)

    def __str__(self):
        return self.municipio_fi, self.ano_fi
