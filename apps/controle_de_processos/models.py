from django.db import models
from apps.core.models import Base
from apps.municipios.models import Municipio
from apps.funcionarios.models import Funcionario

class Contribuinte(models.Model):
    tipo_pessoas = (
        ('FÍSICA', 'FÍSICA'), ('JURÍDICA', 'JURÍDICA'),
    )
        
    nome_contribuinte = models.CharField(max_length=200)
    tipo_pessoa = models.CharField(max_length=50, choices=tipo_pessoas)
    documento = models.CharField(max_length=20, verbose_name='CPF/CNPJ')
    nome_fantasia = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(max_length=50, blank=True, null=True)
    cep = models.CharField(max_length=11)
    logradouro = models.CharField(max_length=100, blank=True, null=True)
    numero_casa = models.CharField(max_length=20, blank=True, null=True)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True) 
    localidade = models.CharField(max_length=100, blank=True, null=True)
    uf_contri = models.CharField(max_length=2, verbose_name='UF', blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    celular = models.CharField(max_length=20, blank=True, null=True)
    origem = models.CharField(max_length=20, default='usuário', blank=True, null=True)

    def __str__(self):
        return self.nome_contribuinte


class TipoProcesso(Base):
    tipo = models.CharField(max_length=100)

    def __str__(self):
        return self.tipo

class Processo(Base):
    uf = (
        ('MS', 'MS'),
    )
    
    numero = models.CharField(verbose_name='N°', max_length=10)
    contribuinte = models.ForeignKey(Contribuinte, on_delete=models.SET_NULL, null=True)
    municipio = models.ForeignKey(Municipio, on_delete=models.PROTECT)
    uf = models.CharField(max_length=2, choices=uf, default='MS')
    data_div_ativa = models.DateField(blank=True, null=True)
    valor_tributo = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    valor_multa = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    valor_credito = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    valor_atualizado = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    data_valor_atualizado = models.DateField(blank=True, null=True)
    tipo = models.ForeignKey(TipoProcesso, on_delete=models.PROTECT, null=True)
    exercicio = models.IntegerField()
    
    def __str__(self):
        return self.numero
    
class TipoAndamento(Base):
    status = (
        ('Executado', 'Executado'), ('Recebido', 'Recebido'), ('Encerrado', 'Encerrado'), ('Em Andamento', 'Em Andamento'), ('Suspenso', 'Suspenso')
    )
    codigo = models.CharField(max_length=10, blank=True, null=True)
    tipo_andamento = models.CharField(max_length=100, verbose_name='Tipo de Andamento')
    status = models.CharField(max_length=20, choices=status)
    prazo = models.BooleanField(default=False) 
    pagamento = models.BooleanField(default=False)
    encaminhamento = models.BooleanField(default=False)
    numero_aiti = models.BooleanField(default=False)
    avaliacao_imobiliaria = models.BooleanField(default=False)
    criar_atendimento = models.BooleanField(default=False)

    def __str__(self):
        return self.tipo_andamento
    
class LocalizacaoProcesso(models.Model):
    localizacao = models.CharField(max_length=70, blank=True, null=True)

    def __str__(self):
        return self.localizacao

class Andamento(Base):
    situacao = (
        ('Sem Pagamento', 'Sem Pagamento'), ('Com Pagamento', 'Com Pagamento'), ('Registrado no andamento "Avaliação Imobiliária"', 'Registrado no andamento "Avaliação Imobiliária"')
    )

    processo = models.ForeignKey(Processo, on_delete=models.CASCADE)
    sequencial = models.IntegerField(default=1, blank=True, null=True)
    data_andamento = models.DateField()
    tipo_andamento = models.ForeignKey(TipoAndamento, on_delete=models.PROTECT, null=True)
    situacao_pagamento = models.CharField(max_length=200, choices=situacao, blank=True, null=True) 
    valor_pago = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    numero_aiti = models.CharField(max_length=10, blank=True, null=True)
    data_aiti = models.DateField(blank=True, null=True)
    dias_data_prazo = models.IntegerField(blank=True, null=True)
    data_prazo = models.DateField(blank=True, null=True)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, blank=True, null=True)
    localizacao_processo = models.ForeignKey(LocalizacaoProcesso, on_delete=models.SET_NULL, blank=True, null=True)
    data_recebimento = models.DateField(blank=True, null=True)
    obs = models.TextField(max_length=2000, blank=True, null=True)
    arquivo = models.FileField(upload_to='arquivo/', blank=True, null=True) 
    arquivo2 = models.FileField(upload_to='arquivo/', blank=True, null=True)

    def __str__(self):
        return str(self.sequencial)

class ArquivoAndamento(Base):
    andamento = models.ForeignKey(Andamento, related_name='andamento_upload', on_delete=models.CASCADE)
    arquivo = models.FileField(upload_to='arquivo/')

    def __str__(self):
        return self.andamento
    
class TipoAndamentoAvaliacao(Base):
    tipo_and_aval = models.CharField(max_length=100)

    def __str__(self):
        return self.tipo_and_aval

class TipoOperacao(models.Model):
    calculo_operacao = (
        (f'sobre diferença', f'sobre diferença'), 
        (f'sobre maior valor', f'sobre maior valor'),
        (f'sobre valor declarado', f'sobre valor declarado')
    )

    tipo_ope_aval = models.CharField(max_length=40)
    calculo_operacao_aval = models.CharField(max_length=100, choices=calculo_operacao, blank=True, null=True)

    def __str__(self):
        return self.tipo_ope_aval

class TipoFinalidade(models.Model):
    tipo_finalidade = models.CharField(max_length=40)

    def __str__(self):
        return self.tipo_finalidade

class Avaliacao(Base):
    andamento = models.ForeignKey(Andamento, on_delete=models.CASCADE, blank=True, null=True)
    sequencial = models.IntegerField(default=1, blank=True, null=True)
    matricula = models.CharField(max_length=20, blank=True, null=True)
    area = models.DecimalField(decimal_places=4, max_digits=12, blank=True, null=True)
    finalidade = models.ForeignKey(TipoFinalidade, on_delete=models.PROTECT, blank=True, null=True)
    data_pedido = models.DateField(blank=True, null=True)
    data_avaliacao = models.DateField(blank=True, null=True)
    tipo_andamento_avaliacao = models.ForeignKey(TipoAndamentoAvaliacao, on_delete=models.PROTECT, blank=True, null=True)
    operacao = models.ForeignKey(TipoOperacao, on_delete=models.PROTECT, blank=True, null=True)
    responsavel = models.ForeignKey(Funcionario, on_delete=models.PROTECT, blank=True, null=True)
    valor_declarado = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    valor_avaliado = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    valor_itbi_diferenca = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    valor_pago_avaliacao = models.DecimalField(decimal_places=2, max_digits=11, blank=True, null=True)
    data_valor_pago = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.matricula