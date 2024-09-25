from django.db import models
from apps.core.models import Base
from apps.municipios.models import Municipio
from apps.controle_de_processos.models import Andamento
from django.contrib.auth.models import User


from apps.controle_de_processos.models import Processo

class TipoContato(models.Model):
    contato = models.CharField(max_length=30)

    def __str__(self):
        return self.contato
    
class TipoAtendimento(models.Model):
    atendimento = models.CharField(max_length=250)
    codigo = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.atendimento
    
class ClienteAtendimento(models.Model):
    nome_cliente = models.CharField(max_length=50)
    usuario_criador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.nome_cliente

class StatusAtendimento(models.Model):
    nome = models.CharField(max_length=20)

    def __str__(self):
        return self.nome
    
class Atendimento(Base):    
    ticket = models.CharField(max_length=20)   
    atendimento_processo = models.CharField(max_length=10, blank=True, null=True)
    processo_atendimento = models.ForeignKey(Processo, on_delete=models.SET_NULL, blank=True, null=True)
    andamento_atendimento = models.ForeignKey(Andamento, on_delete=models.CASCADE, blank=True, null=True)
    municipio_atendimento = models.ForeignKey(Municipio, on_delete=models.CASCADE)
    data_atendimento = models.DateField()
    contato = models.ForeignKey(TipoContato, on_delete=models.SET_NULL, blank=True, null=True)
    atendimento = models.ForeignKey(TipoAtendimento, related_name='tipo_atendimento', on_delete=models.PROTECT)
    cliente_atendimento = models.ForeignKey(ClienteAtendimento, on_delete=models.PROTECT)
    descricao_atendimento = models.TextField(max_length=2000)
    tempo = models.CharField(max_length=10, blank=True, null=True)
    status = models.ForeignKey(StatusAtendimento, on_delete=models.PROTECT)

    def __str__(self):
        return self.atendimento_processo
    
