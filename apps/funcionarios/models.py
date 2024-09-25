from django.db import models
from apps.core.models import Base
from django.contrib.auth.models import User
from apps.empresa.models import Empresa
from apps.municipios.models import Municipio

class Departamento(Base):
    departamento = models.CharField(max_length=30)
    
    def __str__(self):
        return self.departamento

class Funcionario(Base):
    user = models.OneToOneField(User, related_name='funcionario_user', on_delete=models.PROTECT)
    nome = models.CharField(max_length=100)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT, blank=True, null=True) 
    assinatura = models.ImageField(upload_to='assinaturas/', blank=True, null=True)

    def __str__(self):
        return self.nome
    