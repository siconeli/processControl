from django.db import models
from django.contrib.auth.models import User
from apps.core.models import Base

class Empresa(Base):
    razao_social = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=20)
    logradouro = models.CharField(max_length=50)
    numero = models.CharField(max_length=20)
    cep = models.CharField(max_length=11)
    bairro = models.CharField(max_length=50)
    municipio = models.CharField(max_length=50)
    uf = models.CharField(max_length=2)
    
    def __str__(self):
        return self.razao_social