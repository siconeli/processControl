from django.db import models

from django.contrib.auth.models import User

class Base(models.Model):
    ativo = models.BooleanField('Ativo', default=True)
    data_criacao = models.DateField('data_criação', auto_now_add=True)
    usuario_criador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    data_alteracao = models.DateField('Alterado', auto_now=True)
    origem = models.CharField(max_length=20, default='usuario', blank=True, null=True)

    class Meta:
        abstract = True

class AuditoriaProcessoDelete(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    objeto_id = models.PositiveIntegerField()
    tipo_objeto = models.CharField(max_length=255)
    view = models.CharField(max_length=255)  
    acao = models.CharField(max_length=255) 
    processo = models.CharField(max_length=255, blank=True, null=True)
    municipio = models.CharField(max_length=255, blank=True, null=True)
    data_hora = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ('-data_hora',)

class AuditoriaProcessoUpdate(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    objeto_id = models.PositiveIntegerField()
    tipo_objeto = models.CharField(max_length=255)
    view = models.CharField(max_length=255)  
    acao = models.CharField(max_length=255) 
    numero_antigo = models.CharField(max_length=255, blank=True, null=True)
    numero_novo = models.CharField(max_length=255, blank=True, null=True)
    municipio = models.CharField(max_length=255, blank=True, null=True)
    data_hora = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ('-data_hora',)

class AuditoriaAndamentoDelete(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    objeto_id = models.PositiveIntegerField()
    tipo_objeto = models.CharField(max_length=255)
    view = models.CharField(max_length=255)  
    acao = models.CharField(max_length=255) 
    processo = models.CharField(max_length=255, blank=True, null=True)
    municipio = models.CharField(max_length=255, blank=True, null=True)
    andamento = models.CharField(max_length=255, blank=True, null=True)
    data_hora = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ('-data_hora',)
