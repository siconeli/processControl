from django.db import models
from apps.municipios.models import Municipio

class Receita(models.Model):
    nome = models.CharField(max_length=50)

    def __str__(self):
        return self.nome
    
class Ano(models.Model):
    nome = models.CharField(max_length=4)

    def __str__(self):
        return self.nome

class Ficha(models.Model):
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE)
    receita = models.ForeignKey(Receita, on_delete=models.CASCADE)
    ano = models.ForeignKey(Ano, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.municipio}, {self.receita}, {self.ano}'
    
class ValorMes(models.Model):
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE)
    janeiro = models.DecimalField(decimal_places=2, max_digits=11)
    fevereiro = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    marco = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    abril = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    maio = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    junho = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    julho = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    agosto = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    setembro = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    outubro = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    novembro = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    dezembro = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)

    def __str__(self):
        return f'{self.janeiro}, {self.fevereiro}'