from .forms import ContribuinteForm, ProcessoForm, AvaliacaoForm
from .models import Processo, Andamento, Avaliacao, TipoAndamento, Contribuinte, TipoProcesso, ArquivoAndamento, TipoOperacao,TipoAndamentoAvaliacao
from apps.municipios.models import Municipio
from apps.funcionarios.models import Funcionario
from apps.core.models import AuditoriaProcessoDelete, AuditoriaAndamentoDelete, AuditoriaProcessoUpdate
from apps.registro.models import Atendimento, TipoAtendimento
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic import DetailView, View, TemplateView
from django.contrib.auth.models import User
from django.urls import reverse, reverse_lazy 
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
import os
from datetime import date, datetime, timedelta
from django.http import HttpResponse
from django.conf import settings
import uuid
from django.db.models import Max
import decimal
from django.http import JsonResponse
import uuid
from django.core.files.base import ContentFile
import subprocess
import tempfile
from fpdf import FPDF
import tempfile
import os
from django.core.cache import cache

# PROCESSO 
class ProcessoCreate(LoginRequiredMixin, CreateView):
    model = Processo
    template_name = 'processos/processo_create.html'
    form_class = ProcessoForm

    def form_valid(self, form):
        try:
            form.instance.usuario_criador = self.request.user 

            contribuinte_form = ContribuinteForm(self.request.POST)

            if contribuinte_form.is_valid():
                numero_processo = form.cleaned_data['numero']
                municipio = form.cleaned_data['municipio']
                    
                if Processo.objects.filter(numero=numero_processo, municipio=municipio, ativo=True).exists(): 
                    form.add_error(None, f'Já existe um processo com o número {numero_processo} registrado neste município!')
        
                    return self.form_invalid(form)
                
                input_documento = contribuinte_form.cleaned_data['documento']
                
                cad_contribuinte = Contribuinte.objects.filter(documento=input_documento).exists()
                if cad_contribuinte:
                    inputs = {
                        'input_nome_contribuinte': 'nome_contribuinte',
                        'input_tipo_pessoa': 'tipo_pessoa',
                        'input_documento': 'documento',
                        'input_nome_fantasia': 'nome_fantasia',
                        'input_email': 'email',
                        'input_cep': 'cep',
                        'input_logradouro': 'logradouro',
                        'input_numero_casa': 'numero_casa',
                        'input_complemento': 'complemento',
                        'input_bairro': 'bairro',
                        'input_localidade': 'localidade',
                        'input_uf_contri': 'uf_contri',
                        'input_telefone': 'telefone',
                        'input_celular': 'celular'
                    }
                    contribuinte = Contribuinte.objects.filter(documento=input_documento).last()
                    for atributo in inputs.values():
                        contribuinte_value = getattr(contribuinte, atributo, None) 
                        input_cleaned = contribuinte_form.cleaned_data[atributo]
                        if contribuinte_value is not None and input_cleaned is not None:
                            if input_cleaned != contribuinte_value:
                                setattr(contribuinte, atributo, input_cleaned) 
                        elif contribuinte_value is None and input_cleaned is not None:
                            setattr(contribuinte, atributo, input_cleaned) 
                        elif contribuinte_value is not None and input_cleaned is None: 
                            setattr(contribuinte, atributo, '')

                    contribuinte.save()
                    processo = form.save(commit=False)
                    processo.contribuinte = contribuinte
                    processo.save()
                    return super().form_valid(form)

                contribuinte = contribuinte_form.save()
                processo = form.save(commit=False)
                processo.contribuinte = contribuinte
                processo.save()

                return super().form_valid(form)
        
            else:
                form.add_error(None, 'Erro no formulário de contribuinte.')

                return self.form_invalid(form)
            
        except Exception as error:
            print(f'Error na funcao (form_valid) - views: (ProcessoCreate) - error: {str(error)}')
        
    def get_form(self, form_class=None):
        try:
            form = super().get_form(form_class)
            form.fields['municipio'].queryset = Municipio.objects.filter(tipo_contrato='Assessoria', origem='usuario', ativo=True).order_by('nome')
            form.fields['tipo'].queryset = TipoProcesso.objects.filter(ativo=True).exclude(id=8).order_by('tipo')

            return form
        
        except Exception as error:
            print(f'Error na funcao (get_form) - views: (ProcessoCreate) - error: {str(error)}')
            return HttpResponse('httpresponse/teste.html')
    
    def get_success_url(self):
        try:
            ultimo_processo_banco_de_dados = Processo.objects.latest('id')
            id_processo_em_criacao = ultimo_processo_banco_de_dados.id 

            cache.delete(f'processos_filtrados_{self.request.user.id}') 

            return reverse('andamento-list', args=[id_processo_em_criacao])
        
        except Exception as error:
            print(f'Error na funcao (get_success_url) - views: (ProcessoCreate) - error: {str(error)}')    
    
    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context['contribuinte_form'] = ContribuinteForm()

            return context
        
        except Exception as error:
            print(f'Error na funcao (get_context_data) - views: (ProcessoCreate) - data: {datetime.now()} - error: {str(error)}')

class BuscaDocumento(View):
    def get(self, request):
        documento = request.GET.get('documento', None)
        documento = documento.replace(".", " ").replace("-", " ").replace("/", " ")
        documento = ''.join(documento.split())
        if documento:
            try:
                contribuinte = Contribuinte.objects.filter(documento=documento).last()
                data={
                    'k_nome_contribuinte': contribuinte.nome_contribuinte,
                    'k_tipo_pessoa': contribuinte.tipo_pessoa,
                    'k_documento': contribuinte.documento,
                    'k_nome_fantasia': contribuinte.nome_fantasia,
                    'k_email': contribuinte.email,
                    'k_cep': contribuinte.cep,
                    'k_logradouro': contribuinte.logradouro,
                    'k_numero_casa': contribuinte.numero_casa,
                    'k_complemento': contribuinte.complemento,
                    'k_bairro': contribuinte.bairro,
                    'k_localidade': contribuinte.localidade,
                    'k_uf_contri': contribuinte.uf_contri,
                    'k_telefone': contribuinte.telefone,
                    'k_celular': contribuinte.celular
                }
                return JsonResponse(data)
            except:
                return JsonResponse({'error': 'Contribuinte não cadastrado'}, status=400)
        else:
            return JsonResponse({'error': 'Parâmetro CPF não fornecido'}, status=400)

class ProcessoDetailView(LoginRequiredMixin, DetailView):
    """
        A DetailView é uma view própria para exibir dados de um único objeto, não sendo necessário iterar sobre uma queryset, no template html, é só utilizar o nome da Model em letra minúscula, em seguida utilizar o ponto e o nome do atributo.
        Exemplo: processo.numero
    """
    model = Processo
    template_name = 'processos/processo_detail_view.html'

    def get_object(self, queryset=None):
        try:
            processo_id = self.kwargs.get('id')

            return self.model.objects.get(id=processo_id)

        except Exception as error:
            print(f'Error na funcao (get_object) - views: (ProcessoDetailView) - error: {str(error)}')    

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)

            processo = context['object']

            if processo.valor_tributo:
                valor_tributo = '{:,.2f}'.format(processo.valor_tributo).replace(',', 'X').replace('.', ',').replace('X', '.')
            else:
                valor_tributo = None

            if processo.valor_multa:
                valor_multa = '{:,.2f}'.format(processo.valor_multa).replace(',', 'X').replace('.', ',').replace('X', '.')
            else:
                valor_multa = None

            if processo.valor_credito:
                valor_credito = '{:,.2f}'.format(processo.valor_credito).replace(',', 'X').replace('.', ',').replace('X', '.')
            else:
                valor_credito = None

            if processo.valor_atualizado:
                valor_atualizado = '{:,.2f}'.format(processo.valor_atualizado).replace(',', 'X').replace('.', ',').replace('X', '.')
            else:
                valor_atualizado = None

            context['valor_tributo'] = valor_tributo
            context['valor_multa'] = valor_multa
            context['valor_credito'] = valor_credito
            context['valor_atualizado'] = valor_atualizado

            return context
        
        except Exception as error:
            print(f'Error na funcao (get_context_data) - views: (ProcessoDetailView) - error: {str(error)}')
    
class ProcessoUpdate(LoginRequiredMixin, UpdateView):
    model = Processo
    template_name = 'processos/processo_update.html'
    fields = ['numero', 'municipio', 'uf', 'data_div_ativa', 'valor_tributo', 'valor_multa', 'valor_credito', 'valor_atualizado', 'data_valor_atualizado', 'tipo', 'exercicio']
    success_url = reverse_lazy('processo-list')

    def form_valid(self, form):
        try:
            processo = self.get_object()
            contribuinte = Contribuinte.objects.get(id=processo.contribuinte_id)
            contribuinte_form = ContribuinteForm(self.request.POST, instance=contribuinte)

            numero_input = form.cleaned_data['numero']
            municipio_input = form.cleaned_data['municipio']

            if processo.numero != numero_input:
                if Processo.objects.filter(numero=numero_input, municipio=municipio_input, ativo=True).exists(): 
                    form.add_error(None, f'Já existe um processo com o número {numero_input} registrado neste município!') 
        
                    return self.form_invalid(form)
                
                AuditoriaProcessoUpdate.objects.create(
                    usuario = self.request.user,
                    objeto_id = processo.id,
                    tipo_objeto = 'processo',
                    view = ProcessoUpdate,
                    acao = 'update',
                    numero_antigo = processo.numero,
                    numero_novo = numero_input,
                    municipio = processo.municipio,
                )

            if contribuinte_form.is_valid():
                contribuinte_form.save()

                return super().form_valid(form)
        
            else:
                form.add_error(None, 'Erro no formulário de contribuinte.')

                return self.form_invalid(form)
            
        except Exception as error:
            print(f'Error na funcao (form_valid) - views: (ProcessoUpdate) - error: {str(error)}')

    def get_object(self, queryset=None):
        try:
            processo_id = self.kwargs.get('id')

            return self.model.objects.get(id=processo_id)
        
        except Exception as error:
            print(f'Error na funcao (get_object) - views: (ProcessoUpdate) - error: {str(error)}')
    
    def get_form(self, form_class=None):
        try:
            form = super().get_form(form_class)
            form.fields['municipio'].queryset = Municipio.objects.filter(tipo_contrato='Assessoria', ativo=True).order_by('nome')

            return form
        
        except Exception as error:
            print(f'Error na funcao (get_form) - views: (ProcessoUpdate) - error: {str(error)}')

    def get_context_data(self, **kwargs):
        try:
            processo_id = self.kwargs.get('id')
            processo = Processo.objects.get(id=processo_id)
            contribuinte = Contribuinte.objects.get(id=processo.contribuinte_id)

            if contribuinte.nome_contribuinte is None:
                contribuinte.nome_contribuinte = ""
            
            if contribuinte.tipo_pessoa is None:
                contribuinte.tipo_pessoa = ""
            
            if contribuinte.documento is None:
                contribuinte.documento = ""
            
            if contribuinte.nome_fantasia is None:
                contribuinte.nome_fantasia = ""
            
            if contribuinte.email is None:
                contribuinte.email = ""
            
            if contribuinte.cep is None:
                contribuinte.cep = ""
            
            if contribuinte.logradouro is None:
                contribuinte.logradouro = ""
            
            if contribuinte.numero_casa is None:
                contribuinte.numero_casa = ""
            
            if contribuinte.complemento is None:
                contribuinte.complemento = ""

            if contribuinte.bairro is None:
                contribuinte.bairro = ""

            if contribuinte.localidade is None:
                contribuinte.localidade = ""

            if contribuinte.uf_contri is None:
                contribuinte.uf_contri = ""

            if contribuinte.telefone is None:
                contribuinte.telefone = ""

            if contribuinte.celular is None:
                contribuinte.celular = ""

            context = super().get_context_data(**kwargs)

            context['contribuinte'] = contribuinte

            return context
        
        except Exception as error:
            print(f'Error na funcao (get_context_data) - views: (ProcessoUpdate) - error: {str(error)}')

    def get_success_url(self) -> str:
        cache.delete(f'processos_filtrados_{self.request.user.id}')
        return super().get_success_url()

class ProcessoDelete(LoginRequiredMixin, DeleteView):
    model = Processo
    success_url = reverse_lazy('processo-list')

    def form_valid(self, form):
        try: 
            processo = self.get_object()

            contribuinte = Contribuinte.objects.get(id=processo.contribuinte_id)
            if contribuinte:
                processos_contribuinte = Processo.objects.filter(contribuinte_id=contribuinte.id)
                if processos_contribuinte:
                    if len(processos_contribuinte) == 1:
                        contribuinte.delete()   
        
            AuditoriaProcessoDelete.objects.create(
                usuario = self.request.user,
                objeto_id = self.object.id,
                tipo_objeto = 'processo administrativo',
                view = Processo,
                acao = 'delete',
                processo = self.object.numero,
                municipio = processo.municipio
                )
        
            return super().form_valid(form)
        
        except Exception as error:
            print(f'Error na funcao (form_valid) - views: (ProcessoDelete) - error: {str(error)}')

    def get_object(self, queryset=None):
        try:
            processo_id = self.kwargs.get('id')
          
            return self.model.objects.get(id=processo_id)

        except Exception as error:
            print(f'Error na funcao (get_object) - views: (ProcessoDelete) - error: {str(error)}')

    def get_success_url(self) -> str:
        cache.delete(f'processos_filtrados_{self.request.user.id}')
        return super().get_success_url()

class ProcessoList(LoginRequiredMixin, ListView):
    model = Processo
    template_name = 'processos/processo_list.html'

    def get_queryset(self):
        id_usuario = self.request.user.id

        filtros = {
            'numero': 'cache_key_numero',
            'tipo': 'cache_key_tipo',
            'contribuinte': 'cache_key_contribuinte',
            'documento': 'cache_key_documento', 
            'municipio': 'cache_key_municipio',
            'criador': 'cache_key_criador',
            'matricula': 'cache_key_matricula',
            'exercicio': 'cache_key_exercicio'
        }

        for filtro, key_cache in filtros.items():
            valor_filtro = self.request.GET.get(filtro)
            key_cache_id = f'{key_cache}_{id_usuario}'
            if valor_filtro == '':
                cache.delete(key_cache_id)
            elif valor_filtro:
                cache.set(key_cache_id, valor_filtro)
        
        filtro_numero = self.request.GET.get("numero")
        filtro_tipo = self.request.GET.get("tipo")
        filtro_contribuinte = self.request.GET.get("contribuinte")
        filtro_documento = self.request.GET.get("documento")
        filtro_municipio = self.request.GET.get("municipio")
        filtro_criador = self.request.GET.get("criador")
        matricula = self.request.GET.get("matricula")
        filtro_exercicio = self.request.GET.get("exercicio")

        key_cache_processos_filtrados = f'processos_filtrados_{self.request.user.id}'
        cache_processos_filtrados = cache.get(key_cache_processos_filtrados)

        if filtro_numero and filtro_municipio or filtro_tipo and filtro_municipio or filtro_contribuinte and filtro_municipio or filtro_documento and filtro_municipio or filtro_criador and filtro_municipio or matricula and filtro_municipio or filtro_exercicio and filtro_municipio: 
            processos_filtrados = self.model.objects.filter(ativo=True)
            
            if filtro_numero:
                processos_filtrados = processos_filtrados.filter(numero__icontains=filtro_numero)
    
            if filtro_tipo:
                processos_filtrados = processos_filtrados.filter(tipo_id=filtro_tipo)

            if filtro_contribuinte:
                processos_filtrados = processos_filtrados.filter(contribuinte__nome_contribuinte__icontains=filtro_contribuinte)

            if filtro_documento:
                processos_filtrados = processos_filtrados.filter(contribuinte__documento__icontains=filtro_documento)

            if filtro_municipio:
                processos_filtrados = processos_filtrados.filter(municipio_id=filtro_municipio)

            if filtro_criador:
                processos_filtrados = processos_filtrados.filter(usuario_criador_id=filtro_criador)

            if matricula:
                processos_filtrados = processos_filtrados.filter(andamento__avaliacao__matricula__icontains=matricula).distinct()

            if filtro_exercicio:
                processos_filtrados = processos_filtrados.filter(exercicio=filtro_exercicio)

        elif cache_processos_filtrados is not None:
            processos_filtrados = cache_processos_filtrados

        elif cache.get(f'cache_key_numero_{id_usuario}') or cache.get(f'cache_key_tipo_{id_usuario}') or cache.get(f'cache_key_contribuinte_{id_usuario}') or cache.get(f'cache_key_documento_{id_usuario}') or cache.get(f'cache_key_municipio_{id_usuario}') or cache.get(f'cache_key_criador_{id_usuario}'):
            processos_filtrados = self.model.objects.filter(ativo=True)

            get_cache_key_numero = cache.get(f'cache_key_numero_{id_usuario}')
            get_cache_key_tipo = cache.get(f'cache_key_tipo_{id_usuario}')
            get_cache_key_contribuinte = cache.get(f'cache_key_contribuinte_{id_usuario}')
            get_cache_key_documento = cache.get(f'cache_key_documento_{id_usuario}')
            get_cache_key_municipio = cache.get(f'cache_key_municipio_{id_usuario}')
            get_cache_key_criador = cache.get(f'cache_key_criador_{id_usuario}')
            get_cache_key_matricula = cache.get(f'cache_key_matricula_{id_usuario}')
            get_cache_key_exercicio = cache.get(f'cache_key_exercicio_{id_usuario}')

            if get_cache_key_numero:
                processos_filtrados = processos_filtrados.filter(numero__icontains=get_cache_key_numero)

            if get_cache_key_tipo:
                processos_filtrados = processos_filtrados.filter(tipo_id=get_cache_key_tipo)

            if get_cache_key_contribuinte:
                processos_filtrados = processos_filtrados.filter(contribuinte__nome_contribuinte__icontains=get_cache_key_contribuinte)

            if get_cache_key_documento:
                processos_filtrados = processos_filtrados.filter(contribuinte__documento__icontains=get_cache_key_documento)

            if get_cache_key_municipio:
                processos_filtrados = processos_filtrados.filter(municipio_id=get_cache_key_municipio)

            if get_cache_key_criador:
                processos_filtrados = processos_filtrados.filter(usuario_criador_id=get_cache_key_criador)

            if get_cache_key_matricula:
                processos_filtrados = processos_filtrados.filter(andamento__avaliacao__matricula__icontains=get_cache_key_matricula).distinct() 
            
            if get_cache_key_exercicio:
                processos_filtrados = processos_filtrados.filter(exercicio=get_cache_key_exercicio)


        else:
            processos_filtrados = self.model.objects.none()

        cache.set(key_cache_processos_filtrados, processos_filtrados)

        return processos_filtrados

    def get(self, request, *args, **kwargs):
        """
            Se o name 'limpar_filtros' do button submit 'limpar' estiver presente no request do método GET, limpa os filtros da sessão, para limpar a lista de processos.
        """
        if 'limpar_filtros' in request.GET:      
            filtros = ['filtro_numero', 'filtro_tipo', 'filtro_contribuinte', 'filtro_documento', 'filtro_municipio', 'filtro_criador']

            for filtro in filtros:
                if filtro in self.request.session:
                    self.request.session.pop(filtro)
            
            return redirect('processo-list')
        
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            filtros = {
                'numero': 'cache_key_numero',
                'tipo': 'cache_key_tipo',
                'contribuinte': 'cache_key_contribuinte',
                'documento': 'cache_key_documento', 
                'municipio': 'cache_key_municipio',
                'criador': 'cache_key_criador',
                'matricula': 'cache_key_matricula',
                'exercicio': 'cache_key_exercicio'
            }
            for key_cache in filtros.values():
                key_cache_id = f'{key_cache}_{self.request.user.id}' 
                if cache.get(key_cache_id):
                    context[key_cache] = cache.get(key_cache_id)


            usuarios = User.objects.filter(is_superuser=False, is_active=True).exclude(username='migracao').order_by('username')
            for usuario in usuarios:
                usuario.username = usuario.username.upper() 

            context['municipios'] = Municipio.objects.filter(tipo_contrato='Assessoria', ativo=True).order_by('nome')
            context['usuarios'] = usuarios
            context['tipos'] = TipoProcesso.objects.filter(ativo=True).exclude(id=8).order_by('tipo')

            return context
            
        except Exception as error:
            print(f'Error na funcao (get_context_data) - views: (ProcessoList) - error: {str(error)}')
    
class LimparCacheProcessoView(View): 
    def get(self, request):
        filtros = {
            'numero': 'cache_key_numero',
            'tipo': 'cache_key_tipo',
            'contribuinte': 'cache_key_contribuinte',
            'documento': 'cache_key_documento', 
            'municipio': 'cache_key_municipio',
            'criador': 'cache_key_criador',
            'matricula': 'cache_key_matricula',
            'exercicio': 'cache_key_exercicio'
        }
        for key_cache in filtros.values():
            key_cache_id = f'{key_cache}_{self.request.user.id}'
            cache.delete(key_cache_id)
        
        cache.delete(f'processos_filtrados_{self.request.user.id}')
        
        return redirect(reverse('processo-list'))
    
def AtendimentoList(request, id):
    if request.method == 'GET':
        return render(request, 'processos/processo_atendimento_list.html')

def primeiro_dia_mes_anterior():
    hoje = date.today()
    primeiro_dia_mes_atual = hoje.replace(day=1)
    ultimo_dia_mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)
    primeiro_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1)
    return primeiro_dia_mes_anterior

def data_anterior_mes_anterior(data):
    primeiro_dia_mes_anterior_data = primeiro_dia_mes_anterior()
    return data < primeiro_dia_mes_anterior_data

# ANDAMENTO
class AndamentoCreate(LoginRequiredMixin, CreateView):  
    model = Andamento
    template_name = 'andamentos/andamento_create.html'
    fields = ['data_andamento', 'tipo_andamento', 'funcionario', 'localizacao_processo', 'situacao_pagamento', 'valor_pago', 'numero_aiti', 'data_aiti', 'dias_data_prazo', 'data_prazo', 'data_recebimento', 'obs', 'arquivo', 'arquivo2']

    def form_valid(self, form):
        """
            A funcao form_valid() serve para alterar os valores do atributo ou realizar qualquer ação antes que o formulário seja salvo.
        """
        try:
            id_processo = self.kwargs.get('id')
            processo = Processo.objects.get(id=id_processo)
            form.instance.processo_id = id_processo
            form.instance.usuario_criador = self.request.user

            if Atendimento.objects.filter(ativo=True).exists():
                ultimo_id_db = Atendimento.objects.filter(ativo=True).latest('id').id
            else:
                ultimo_id_db = -1

            id_atendimento_atual = ultimo_id_db + 1
            id_atendimento_atual = str(id_atendimento_atual)

            randomico = uuid.uuid4()
            randomico = str(randomico)
            randomico = randomico.upper()
            randomico = randomico.replace('-','')
            randomico = randomico[:3]
            numero_ticket = id_atendimento_atual + randomico

            andamento = form.save()

            if andamento.tipo_andamento.criar_atendimento:
                """
                    Se a data preenchida no campo "Data Andamento" for menor que o mês anterior ao atual, o registro de atendimento é criado com dados x se não é criado com dados y.
                """

                if len(str(processo.numero)) > 4:
                    processo_numero = f'{str(processo.numero)[:-4]}/{str(processo.numero)[-4:]}'
                else:
                    processo_numero = processo.numero

                tipo_atendimento_9 = TipoAtendimento.objects.get(id=9)
                tipo_atendimento_16 = TipoAtendimento.objects.get(id=16)

                if data_anterior_mes_anterior(andamento.data_andamento):
                    data_atendimento_r = andamento.data_criacao
                    tipo_atendimento_r = tipo_atendimento_9
                else:
                    data_atendimento_r = andamento.data_andamento
                    tipo_atendimento_r = tipo_atendimento_16

                atendimento = Atendimento.objects.create(
                    ticket = numero_ticket,
                    atendimento_processo = processo.numero,
                    data_atendimento = data_atendimento_r,
                    descricao_atendimento = f'ATENDIMENTO GERADO A PARTIR DO ANDAMENTO: {str(andamento.tipo_andamento).upper()[:-4]}.\nPROCESSO: {processo_numero}.',
                    municipio_atendimento = processo.municipio,
                    processo_atendimento = processo, 
                    usuario_criador = self.request.user,
                    cliente_atendimento_id = 5,
                    atendimento = tipo_atendimento_r,
                    andamento_atendimento = andamento,
                    status_id = 3
                )
                            
                atendimento.save()

            maior_sequencial = Andamento.objects.filter(processo_id=id_processo).aggregate(max_sequencial=Max('sequencial'))['max_sequencial']

            if maior_sequencial is not None:
                form.instance.sequencial = maior_sequencial + 1

            avaliacao_form = AvaliacaoForm(self.request.POST)

            if avaliacao_form.is_valid():
                input_matricula = avaliacao_form.cleaned_data['matricula']
                input_tipo_operacao = avaliacao_form.cleaned_data['operacao']
                input_valor_declarado = avaliacao_form.cleaned_data['valor_declarado']
                input_valor_avaliado = avaliacao_form.cleaned_data['valor_avaliado']
            
                if input_matricula:
                    aliquota = processo.municipio.aliquota
                    municipio = processo.municipio.nome
                    avaliacoes = Avaliacao.objects.filter(andamento__processo=processo)
                    avaliacao = avaliacao_form.save(commit=False)
                    avaliacao.andamento = andamento
                    avaliacao.usuario_criador = self.request.user

                    maior_sequencial_aval = avaliacoes.aggregate(maior_sequencial_aval=Max('sequencial'))['maior_sequencial_aval']
                    if maior_sequencial_aval is not None:
                        avaliacao.sequencial = maior_sequencial_aval + 1

                    if municipio == 'AMAMBAI':
                        if input_valor_avaliado > 100000 and input_valor_avaliado <= 150000:
                            aliquota = decimal.Decimal('3')
                        elif input_valor_avaliado > 150000:
                            aliquota = decimal.Decimal('3.5')

                    if input_tipo_operacao and input_valor_declarado and input_valor_avaliado:
                        operacao = TipoOperacao.objects.get(tipo_ope_aval=input_tipo_operacao)
                        if operacao.calculo_operacao_aval == 'sobre maior valor':
                            maior_valor = max(input_valor_declarado, input_valor_avaliado)
                            avaliacao.valor_itbi_diferenca = maior_valor * (aliquota/100)
                        elif operacao.calculo_operacao_aval == 'sobre valor declarado':
                            avaliacao.valor_itbi_diferenca = input_valor_declarado * (aliquota/100)
                        elif operacao.calculo_operacao_aval == 'sobre diferença':
                            avaliacao.valor_itbi_diferenca = (input_valor_avaliado - input_valor_declarado) * (aliquota/100)

                    avaliacao.save()
                
            else:
                form.add_error(None, 'Erro no formulário de avaliação')
                return self.form_invalid(form)

            return super().form_valid(form)
        
        except Exception as error:
            print(f'Error na funcao (form_valid) - views: (AndamentoCreate) - error: {str(error)}')
    
    def get_success_url(self):
        try:
            processo_id = self.kwargs.get('id')   

            return reverse('andamento-list', args=[processo_id])

        except Exception as error:
            print(f'Error na funcao (get_success_url) - views: (AndamentoCreate) - error: {str(error)}')

    def get_cancelar(self, processo_id):
        try:
            return reverse('andamento-list', args=[processo_id])
        
        except Exception as error:
            print(f'Error na funcao (get_cancelar) - views: (AndamentoCreate) - error: {str(error)}')
    
    def get_context_data(self, **kwargs):
        try:
            processo_id = self.kwargs.get('id')

            funcionarios = Funcionario.objects.filter(ativo=True, empresa_id=1, departamento_id=1) 

            context = super().get_context_data(**kwargs)
            context['dados_processo'] = Processo.objects.filter(id=processo_id)
            context['funcionarios'] = funcionarios  
            context['cancelar'] = self.get_cancelar(processo_id)
            context['avaliacao_form'] = AvaliacaoForm()

            return context
        
        except Exception as error:
            print(f'Error na funcao (get_context_data) - views: (AndamentoCreate) - error: {str(error)}')
    
    def get_form(self, form_class=None):
        try:
            form = super().get_form(form_class)
            form.fields['tipo_andamento'].queryset = TipoAndamento.objects.filter(origem='usuario', ativo=True).order_by('tipo_andamento')
            form.fields['funcionario'].queryset = Funcionario.objects.filter(ativo=True, empresa_id=1, departamento_id__in= [1, 2]).order_by('nome')
            return form
        
        except Exception as error:
            print(f'Error na funcao (get_form) - views: (AndamentoCreate) - error: {str(error)}')

class AndamentoDetailView(LoginRequiredMixin, DetailView):
    model = Andamento
    template_name ='andamentos/andamento_detail_view.html'

    def get_object(self, queryset=None):
        try:
            andamento_id = self.kwargs.get('id')

            return self.model.objects.get(id=andamento_id)
        
        except Exception as error:
            print(f'Error na funcao (get_object) - views: (AndamentoDetailView) - error: {str(error)}')
        
    def get_voltar(self, processo_id):
        try:
            return reverse('andamento-list', args=[processo_id])
        
        except Exception as error:
            print(f'Error na funcao (get_voltar) - views: (AndamentoDetailView) - error: {str(error)}')

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            andamento_id = self.kwargs.get('id') 
            andamento = Andamento.objects.get(id=andamento_id) 
            processo_id = andamento.processo_id 

            valor_pago = andamento.valor_pago
            if valor_pago:
                valor_pago = '{:,.2f}'.format(valor_pago).replace(',', 'X').replace('.', ',').replace('X', '.')      

            try:
                avaliacao = Avaliacao.objects.get(andamento_id=andamento_id)
                valor_declarado = avaliacao.valor_declarado
                if valor_declarado:
                    valor_declarado = '{:,.2f}'.format(valor_declarado).replace(',', 'X').replace('.', ',').replace('X', '.')
                    context['valor_declarado'] = valor_declarado
                
                valor_avaliado = avaliacao.valor_avaliado
                if valor_avaliado:
                    valor_avaliado = '{:,.2f}'.format(valor_avaliado).replace(',', 'X').replace('.', ',').replace('X', '.')
                    context['valor_avaliado'] = valor_avaliado

                valor_itbi_diferenca = avaliacao.valor_itbi_diferenca
                if valor_itbi_diferenca:
                    valor_itbi_diferenca = '{:,.2f}'.format(valor_itbi_diferenca).replace(',', 'X').replace('.', ',').replace('X', '.')
                    context['valor_itbi_diferenca'] = valor_itbi_diferenca
                
                valor_pago_avaliacao = avaliacao.valor_pago_avaliacao
                if valor_pago_avaliacao:
                    valor_pago_avaliacao = '{:,.2f}'.format(valor_pago_avaliacao).replace(',', 'X').replace('.', ',').replace('X', '.')
                    context['valor_pago_avaliacao'] = valor_pago_avaliacao

                if str(avaliacao.finalidade) == 'Urbano':
                    area_urbana = round(avaliacao.area, 2)
                    avaliacao.area = area_urbana
            except:
                avaliacao = None
            if avaliacao is not None:
                context['avaliacao_object'] = avaliacao

            dados_processo = Processo.objects.filter(id=processo_id) 
            for atributo in dados_processo:
                atributo.contribuinte.nome_contribuinte = atributo.contribuinte.nome_contribuinte[:30]

            context['dados_processo'] = dados_processo
            context['voltar'] = self.get_voltar(processo_id)
            context['dados_andamento'] = Andamento.objects.filter(id=andamento_id) 
            context['valor_pago'] = valor_pago

            return context

        except Exception as error:
            print(f'Error na funcao (get_context_data) - views: (AndamentoDetailView) - error: {str(error)}')

class AndamentoUpdate(LoginRequiredMixin, UpdateView):
    model = Andamento
    template_name = 'andamentos/andamento_update.html'
    fields = ['data_andamento', 'tipo_andamento', 'situacao_pagamento','valor_pago', 'numero_aiti', 'data_aiti', 'data_prazo', 'dias_data_prazo', 'data_recebimento', 'obs', 'funcionario', 'localizacao_processo', 'arquivo', 'arquivo2']

    def form_valid(self, form):
        try:
            andamento_id = self.kwargs.get('id')
            try:
                avaliacao = Avaliacao.objects.get(andamento_id=andamento_id)
            except:
                avaliacao = None
            if avaliacao is not None:
                avaliacao_form = AvaliacaoForm(self.request.POST, instance=avaliacao)
                tipo_anda = form.cleaned_data['tipo_andamento']
                if str(tipo_anda) != 'Avaliação Imobiliária - 05':
                    avaliacao.delete()
                else:
                    if avaliacao_form.is_valid():
                        andamento = Andamento.objects.get(id=andamento_id)
                        processo = Processo.objects.get(id=andamento.processo_id)
                        aliquota = processo.municipio.aliquota
                        municipio = processo.municipio.nome

                        input_tipo_operacao = avaliacao_form.cleaned_data['operacao']
                        input_valor_declarado = avaliacao_form.cleaned_data['valor_declarado']
                        input_valor_avaliado = avaliacao_form.cleaned_data['valor_avaliado']

                        avaliacao = avaliacao_form.save(commit=False)

                        if municipio == 'AMAMBAI':
                            if input_valor_avaliado > 100000 and input_valor_avaliado <= 150000:
                                aliquota = decimal.Decimal('3')
                            elif input_valor_avaliado > 150000:
                                aliquota = decimal.Decimal('3.5')

                        if input_tipo_operacao and input_valor_declarado and input_valor_avaliado:
                            operacao = TipoOperacao.objects.get(tipo_ope_aval=input_tipo_operacao)
                            if operacao.calculo_operacao_aval == 'sobre maior valor':
                                maior_valor = max(input_valor_declarado, input_valor_avaliado)
                                avaliacao.valor_itbi_diferenca = maior_valor * (aliquota/100)
                            elif operacao.calculo_operacao_aval == 'sobre valor declarado':
                                avaliacao.valor_itbi_diferenca = input_valor_declarado * (aliquota/100)
                            elif operacao.calculo_operacao_aval == 'sobre diferença':
                                avaliacao.valor_itbi_diferenca = (input_valor_avaliado - input_valor_declarado) * (aliquota/100)

                        avaliacao.save()
            else:
                pass

            return super().form_valid(form)
        
        except Exception as error:
            print(f'Error na funcao (form_valid) - views: (AndamentoUpdate) - error: {str(error)}')

    def get_object(self, queryset=None):
        try:
            andamento_id = self.kwargs.get('id')

            return self.model.objects.get(id=andamento_id)
        
        except Exception as error:
            print(f'Error na funcao (get_object) - views: (AndamentoUpdate) - error: {str(error)}')

    def get_success_url(self):
        try:
            andamento_id = self.kwargs.get('id')
            andamento = Andamento.objects.get(id=andamento_id)
            processo_id = andamento.processo_id

            return reverse('andamento-list', args=[processo_id])

        except Exception as error:
            print(f'Error na funcao (get_success_url) - views: (AndamentoUpdate) - error: {str(error)}')
    
    def get_cancelar(self, processo_id):
        try:
            return reverse('andamento-list', args=[processo_id])

        except Exception as error:
            print(f'Error na funcao (get_cancelar) - views: (AndamentoUpdate) - error: {str(error)}')

    def get_context_data(self, **kwargs):
        try:
            andamento_id = self.kwargs.get('id')
            andamento = Andamento.objects.get(id=andamento_id) 
            processo_id = andamento.processo_id 
            processo = Processo.objects.get(id=processo_id)
            numero_processo = processo.numero
            funcionarios = Funcionario.objects.filter(ativo=True, empresa_id=1, departamento_id=1)
            
                    
            context = super().get_context_data(**kwargs)
            try:
                avaliacao = Avaliacao.objects.get(andamento_id=andamento_id)
                if str(avaliacao.finalidade) == 'Urbano':
                    area_urbana = round(avaliacao.area, 2)
                    avaliacao.area = area_urbana
            except:
                avaliacao = None

            if avaliacao is not None:
                context['avaliacao_form'] = AvaliacaoForm(instance=avaliacao)
                context['avaliacao_object'] = avaliacao 

            dados_processo = Processo.objects.filter(id=processo_id)
            for atributo in dados_processo:
                atributo.contribuinte.nome_contribuinte = atributo.contribuinte.nome_contribuinte[:30]

            context['dados_processo'] = dados_processo
            context['funcionarios'] = funcionarios
            context['cancelar'] = self.get_cancelar(processo_id)
            context['numero_processo'] = numero_processo
            context['dados_andamento'] = andamento

            return context

        except Exception as error:
            print(f'Error na funcao (get_context_data) - views: (AndamentoUpdate) - error: {str(error)}')
    
    def get_form(self, form_class=None):
        try:
            andamento_id = self.kwargs.get('id')
            andamento = Andamento.objects.get(id=andamento_id)
            tipo_andamento_id = andamento.tipo_andamento_id
            
            form = super().get_form(form_class)
            if tipo_andamento_id == 82:
                form.fields['tipo_andamento'].queryset = TipoAndamento.objects.filter(ativo=True).order_by('tipo_andamento')
            else:
                form.fields['tipo_andamento'].queryset = TipoAndamento.objects.filter(ativo=True).exclude(id=82).order_by('tipo_andamento')

            form.fields['funcionario'].queryset = Funcionario.objects.filter(ativo=True, empresa_id=1, departamento_id=1).exclude(id=15).order_by('nome')

            return form

        except Exception as error:
            print(f'Error na funcao (get_form) - views: (AndamentoUpdate) - error: {str(error)}')

class AndamentoDelete(LoginRequiredMixin, DeleteView):
    model = Andamento

    def get_object(self, queryset=None):
        try:
            andamento_id = self.kwargs.get('id')

            return self.model.objects.get(id=andamento_id)

        except Exception as error:
            print(f'Error na funcao (get_object) - views: (ProcessoDelete) - error: {str(error)}')

    def form_valid(self, form):        
        andamento = self.get_object()

        processo_id = andamento.processo_id
        processo = Processo.objects.get(id=processo_id)

        try:
            AuditoriaAndamentoDelete.objects.create(
                usuario = self.request.user,
                objeto_id = andamento.id,
                tipo_objeto = 'andamento',
                view = AndamentoDelete,
                acao = 'delete',
                processo = andamento.processo,
                andamento = andamento.tipo_andamento,
                municipio = processo.municipio,
            )
            
            return super().form_valid(form)
        
        except Exception as error:
            print(f'Error na funcao (form_valid) - views: (AndamentoDelete) - error: {str(error)}')
    
    def get_success_url(self):
        try:
            andamento_id = self.kwargs.get('id')
            andamento = self.model.objects.get(id=andamento_id)
            processo = andamento.processo_id

            return reverse('andamento-list', args=[processo])

        except Exception as error:
            print(f'Error na funcao (get_success_url) - views: (ProcessoDelete) - error: {str(error)}')

class AndamentoList(LoginRequiredMixin, ListView):
    """
        ListView do template que lista os andamentos do processo para editar, deletar e ver os andamentos.
    """
    model = Processo
    template_name = 'andamentos/andamento_list.html'
    
    def get_queryset(self):
        try:
            id_processo = self.kwargs.get('id')
            processo = Processo.objects.get(id=id_processo)  
            andamentos = processo.andamento_set.filter(ativo=True).order_by('data_andamento', 'sequencial')  

            for indice, andamento in enumerate(andamentos): 
                andamento.ordem = indice + 1

            return andamentos
        
        except Exception as error:
            print(f'Error na funcao (get_queryset) - views: (AndamentoList) - error: {str(error)}')

    def get_context_data(self, **kwargs):
        try:
            processo_id = self.kwargs.get('id') 
            processo = self.model.objects.get(id=processo_id)

            andamentos = processo.andamento_set.all()
            if andamentos:
                maior_data = andamentos.aggregate(max_data=Max('data_andamento'))['max_data']
                maior_data = str(maior_data)
                andamentos_maior_data = andamentos.filter(data_andamento=maior_data)
                maior_sequencial = andamentos_maior_data.aggregate(max_sequencial=Max('sequencial'))['max_sequencial']
                ultimo_andamento = andamentos_maior_data.get(sequencial=maior_sequencial)
                tipo_andamento_id = ultimo_andamento.tipo_andamento_id
                tipo_andamento = TipoAndamento.objects.get(id=tipo_andamento_id)
                andamento_atual = tipo_andamento.tipo_andamento
            else:
                andamento_atual = ''

            encaminhamentos = andamentos.filter(tipo_andamento_id=35)
            if encaminhamentos:
                max_data_enca = encaminhamentos.aggregate(max_data=Max('data_andamento'))['max_data'] 
                maior_data = str(max_data_enca)
                max_seq_enca = encaminhamentos.aggregate(max_sequencial_encaminhamentos=Max('sequencial'))['max_sequencial_encaminhamentos']
                if maior_data:
                    enca_max_data = encaminhamentos.filter(data_andamento=maior_data)
                    max_seq_enca = enca_max_data.aggregate(max_sequencial_encaminhamentos=Max('sequencial'))['max_sequencial_encaminhamentos']
                    ultimo_enca = encaminhamentos.get(data_andamento=max_data_enca, sequencial=max_seq_enca)
                    if ultimo_enca:
                        funcionario_id = ultimo_enca.funcionario_id
                        if funcionario_id:
                            funcionario = Funcionario.objects.get(id=funcionario_id)
                            responsavel = funcionario.nome
                        else:
                            responsavel = ''
            else:
                responsavel = ''

            context = super().get_context_data(**kwargs)

            usuario_logado = self.request.user.funcionario_user
            empresa_id = usuario_logado.empresa_id
            
            if empresa_id == 1 :
                context['acesso_interno'] = "Liberado"

            dados_processo = Processo.objects.filter(id=processo_id) 
            for atributo in dados_processo:
                atributo.contribuinte.nome_contribuinte = atributo.contribuinte.nome_contribuinte[:30]

            context['dados_processo'] = dados_processo
            context['andamento_atual'] = andamento_atual
            context['responsavel'] = responsavel
            context['processo_id'] = processo_id 

            return context
        
        except Exception as error:
            print(f'Error na funcao (get_context_data) - views: (AndamentoList) - error: {str(error)}')

class BuscaAndamentoPeloCodigo(View):
    def get(self, request):
        try:
            cod_tip_and = request.GET.get('cod_tip_and', None)

            if cod_tip_and is not None:
                tip_andamento = TipoAndamento.objects.filter(codigo=cod_tip_and).last()
                tip_andamento_id = tip_andamento.id 

                data={
                'id': tip_andamento_id,
                }

                return JsonResponse(data)
        except:
            return JsonResponse({'error': 'Tipo Andamento não encontrato (BuscaAndamentoPeloCodigo)'}, status=400)

class VerificaMatricula(View):
    def get(self, request):
        try:
            processo_id = request.GET.get('processo_id', None)
            num_matricula = request.GET.get('num_matricula', None)

            if num_matricula is not None and processo_id is not None:
                processo = Processo.objects.get(id=processo_id)
                municipio = Municipio.objects.get(id=processo.municipio_id)
                processos = Processo.objects.filter(municipio_id=municipio.id)
                for proc in processos:
                    avaliacoes = Avaliacao.objects.filter(andamento__processo=proc, matricula=num_matricula)

                    if avaliacoes.exists():
                        mensagem = f'Já existe uma matrícula com número {num_matricula} para o município de {municipio.nome.title()}, ao continuar com o lançamento estará cadastrando uma avaliação para uma matrícula já avaliada.'
                        return JsonResponse({'message': mensagem})
                   
            return JsonResponse({'message': ''})
                
        except Exception as error:
            return JsonResponse({'error': f'Erro ao verificar matrícula: {error}'}, status=400)

class BuscaPrazo(View):
    """
        Se o tipo de andamento tiver o atributo prazo que é booelano como True, os campos de prazo irão aparecer assim que o tipo de andamento for selecionado.
    """
    def get(self, request):
        try:
            id_tipo_andamento = request.GET.get('tip_and_select', None)
            id_tipo_andamento_int = int(id_tipo_andamento)

            if id_tipo_andamento is not None:
                tipo_andamento = TipoAndamento.objects.get(id=id_tipo_andamento_int)
                prazo = tipo_andamento.prazo
        
                data={
                    'prazo': prazo
                }

                return JsonResponse(data)
        except:
            return JsonResponse({'error': 'Tipo Andamento não encontrato (BuscaPrazo)'}, status=400)

class BuscaPagamento(View):
    """
        Se o tipo de andamento tiver o atributo Pagamento que é booelano como True, os campos de Pagamento irão aparecer assim que o tipo de andamento for selecionado.
    """
    def get(self, request):
        try:
            id_tipo_andamento = request.GET.get('tip_and_select', None)
            id_tipo_andamento_int = int(id_tipo_andamento)

            if id_tipo_andamento is not None:
                tipo_andamento = TipoAndamento.objects.get(id=id_tipo_andamento_int)
                pagamento = tipo_andamento.pagamento
        
                data={
                    'pagamento': pagamento,
                }

                return JsonResponse(data)
        except:
            return JsonResponse({'error': 'Tipo Andamento não encontrato (BuscaPagamento)'}, status=400)

class BuscaEncaminhamento(View):
    """
        Se o tipo de andamento tiver o atributo Encaminhamento que é booelano como True, os campos de Encaminhamento irão aparecer assim que o tipo de andamento for selecionado.
    """
    def get(self, request):
        try:
            id_tipo_andamento = request.GET.get('tip_and_select', None) 
            id_tipo_andamento_int = int(id_tipo_andamento)

            if id_tipo_andamento is not None:
                tipo_andamento = TipoAndamento.objects.get(id=id_tipo_andamento_int)
                encaminhamento = tipo_andamento.encaminhamento
        
                data={
                    'encaminhamento': encaminhamento,
                }

                return JsonResponse(data)
        except:
            return JsonResponse({'error': 'Tipo Andamento não encontrato (BuscaEncaminhamento)'}, status=400)

class BuscaNumeroAiti(View): 
    """
        Se o tipo de andamento tiver o atributo numero_aiti que é booelano como True, os campos de numero_aiti irão aparecer assim que o tipo de andamento for selecionado.
    """
    def get(self, request):
        try:
            id_tipo_andamento = request.GET.get('tip_and_select', None) 
            id_tipo_andamento_int = int(id_tipo_andamento)

            if id_tipo_andamento is not None:
                tipo_andamento = TipoAndamento.objects.get(id=id_tipo_andamento_int)
                numero_aiti = tipo_andamento.numero_aiti
        
                data={
                    'numero_aiti': numero_aiti,
                }

                return JsonResponse(data)
        except:
            return JsonResponse({'error': 'Tipo Andamento não encontrato (BuscaNumeroAiti)'}, status=400)

class BuscaAvaliacaoImobiliaria(View):
    """
        Se o tipo de andamento tiver o atributo avaliacao_imobiliaria que é booelano como True, os campos de avaliacao_imobiliaria irão aparecer assim que o tipo de andamento for selecionado.
    """
    def get(self, request):
        try:
            id_tipo_andamento = request.GET.get('tip_and_select', None)
            id_tipo_andamento_int = int(id_tipo_andamento)

            if id_tipo_andamento is not None:
                tipo_andamento = TipoAndamento.objects.get(id=id_tipo_andamento_int)
                avaliacao_imobiliaria = tipo_andamento.avaliacao_imobiliaria
        
                data={
                    'avaliacao_imobiliaria': avaliacao_imobiliaria,
                }

                return JsonResponse(data)
        except:
            return JsonResponse({'error': 'Tipo Andamento não encontrato (BuscaAvaliacaoImobiliaria)'}, status=400)

# RELATÓRIOS 
class RelatoriosProcesso(LoginRequiredMixin, TemplateView):
    model = Processo
    template_name = 'processos/processo_reports.html'

    def get_context_data(self, **kwargs):
        municipios = Municipio.objects.filter(tipo_contrato='Assessoria', ativo=True).order_by('nome')
        tipo = TipoProcesso.objects.filter(ativo=True).exclude(tipo='MIGRACAO').order_by('tipo')

        context = super().get_context_data(**kwargs)
        context['municipios'] = municipios
        context['tipo'] = tipo

        return context

class Estrutura_Pdf(FPDF):
    """
        Configurar o cabeçalho e o rodapé para todos os PDF gerados
    """
    def __init__(self, titulo_relatorio, x_nome_empresa, y_nome_empresa, x_titulo_rel, y_titulo_rel, usuario_gerou, data_gerou, nome_municipio, periodo, x_periodo, y_periodo, andamento_aval, x_andamento, y_andamento):
        super().__init__() 
        self.titulo_relatorio = titulo_relatorio
        self.x_nome_empresa = x_nome_empresa
        self.y_nome_empresa = y_nome_empresa
        self.x_titulo_rel = x_titulo_rel
        self.y_titulo_rel = y_titulo_rel
        self.usuario_gerou = usuario_gerou
        self.data_gerou = data_gerou
        self.nome_municipio = nome_municipio
        self.periodo = periodo
        self.x_periodo = x_periodo
        self.y_periodo = y_periodo
        self.andamento_aval = andamento_aval
        self.x_andamento = x_andamento
        self.y_andamento = y_andamento

    def header(self):
        self.image("static/img/empresa.png", 10, 4, 15)

        self.add_font('Calibri', 'B', fname='fonts/Calibri.ttf', uni=True)
        self.set_font('Calibri', 'B', size=12)
        self.cell(self.x_nome_empresa, self.y_nome_empresa, txt='Empresa Teste', ln=True, align='C')

        self.add_font('Calibri', 'B', fname='fonts/Calibri.ttf', uni=True)
        self.set_font('Calibri', 'B', size=12)
        self.cell(self.x_titulo_rel, self.y_titulo_rel, txt=f'{self.titulo_relatorio} {self.nome_municipio}', ln=True, align='C')
        
        if self.periodo:
            self.set_font('Calibri', 'B', size=10)
            self.cell(self.x_periodo, self.y_periodo, txt=self.periodo, ln=True, align='C')
            self.ln(5)
        
        if self.andamento_aval:
            self.set_font('Calibri', 'B', size=9)
            self.cell(self.x_andamento, self.y_andamento, txt=self.andamento_aval, ln=True, align='C')
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.add_font('Calibri', 'B', fname='fonts/Calibri.ttf', uni=True)
        self.set_font('Calibri', 'B', 8)

        self.cell(0, 10, f'Página {self.page_no()}', align="C")
        self.cell(0, 10, f'Usuário: {self.usuario_gerou}  {self.data_gerou}  -  Empresa Teste ', 0, 0, 'R')

import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg') 

class RelatorioGrafico(LoginRequiredMixin, View):
    def get(self, request):
        pdf = FPDF()
        pdf.add_page()

        pdf.image('static/img/layout.png', 0, 0, 210, 297)

        
        categorias = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        valores = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10 , 11, 0]
        
        largura_colunas = 0.8

        plt.figure(figsize=(20,10))

        plt.bar(categorias, valores, width=largura_colunas)
        
        plt.title('Gráfico de arrecadação de tributos')
        
        plt.ylabel('Valores')
        
        plt.xlabel('Meses')
        
        plt.savefig('static/img/grafico.png')
        
        plt.close()

        pdf.image('static/img/grafico.png', -10, 40, 230) #x=30, y=40, tamanho imagem=200

        pdf.set_font("Arial", size=12)  # Defina a fonte e o tamanho

        # Adicione uma célula com o texto
        pdf.cell(200, 10, txt="Relatório de arrecadação de tributos", ln=True, align='C')

        # Crie um arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf.output(temp_file.name)

        temp_file.close()
        
        with open(temp_file.name, 'rb') as file:
            pdf_content = file.read()
        
        os.unlink(temp_file.name)  # Exclua o arquivo temporário

        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="grafico.pdf"'

        return response


class RelatorioProcessosPorStatus(LoginRequiredMixin, View):
    model = Processo

    def get(self, request, *args, **kwargs):
        try:
            usuario_gerou = self.request.user
                    
            data_atual = datetime.now()
            data_gerou = data_atual - timedelta(hours=1)
            data_gerou = data_gerou.strftime("%d/%m/%Y %H:%M:%S")

            filtro_municipio = request.GET.get('municipio')
            filtro_execucao = request.GET.get('executado')
            filtro_recebido = request.GET.get('recebido')
            filtro_andamento = request.GET.get('andamento')
            filtro_encerrado = request.GET.get('encerrado')
            filtro_colunas = request.GET.get('colunas')
            filtro_exercicio_ini = request.GET.get('exercicio_ini')
            filtro_exercicio_fin = request.GET.get('exercicio_fin')
            filtro_tipo = request.GET.get('tipo')

            try:
                processos_filtrados = Processo.objects.filter(municipio_id=filtro_municipio, ativo=True).order_by('id')
            except:
                processos_filtrados = Processo.objects.none()

            if processos_filtrados:
                if filtro_exercicio_ini and filtro_exercicio_fin:
                    processos_filtrados = processos_filtrados.filter(exercicio__gte=filtro_exercicio_ini, exercicio__lte=filtro_exercicio_fin)
                
                elif filtro_exercicio_ini:
                    processos_filtrados = processos_filtrados.filter(exercicio=filtro_exercicio_ini)
                
                elif filtro_exercicio_fin:
                    processos_filtrados = processos_filtrados.filter(exercicio=filtro_exercicio_fin)

                if filtro_tipo:
                    processos_filtrados = processos_filtrados.filter(tipo_id=filtro_tipo)

            if filtro_municipio:
                get_municipio = Municipio.objects.get(id=filtro_municipio)
                nome_municipio = get_municipio.nome
            else:
                nome_municipio = ''

            x_nome_empresa = 187
            y_nome_empresa = -5
            x_titulo_rel = 188
            y_titulo_rel = 15
            titulo_relatorio = 'Relatório de Processos do Município de'

            periodo = ''
            x_periodo = ''
            y_periodo = ''

            andamento_aval = ''
            x_andamento = ''
            y_andamento = '' 


            pdf = Estrutura_Pdf(titulo_relatorio, x_nome_empresa, y_nome_empresa, x_titulo_rel, y_titulo_rel, usuario_gerou, data_gerou, nome_municipio, periodo, x_periodo, y_periodo, andamento_aval, x_andamento, y_andamento) 
            pdf.add_page()  
        
            # -------------------------------------------------------------------------------
            #  PROCESSOS - STATUS EM EXECUÇÃO
            def cabecalhoExecucao(pdf):
                pdf.set_font('Arial', 'B', size=12)
                pdf.cell(200, 10, 'Processos em Execução', align='C')
                pdf.ln(10)

                pdf.set_font('Arial', 'B', size=10)
                pdf.set_draw_color(0, 0, 0) 
                pdf.set_line_width(0.3) 

                pdf.set_fill_color(211,211,211) 
                pdf.cell(115, 5, 'Empresa', 1, align='C', fill=True) 
                pdf.cell(22, 5, 'Processo', 1, align='C', fill=True) 
                pdf.cell(31, 5, 'Crédito', 1, align='C', fill=True)
                pdf.cell(20, 5, 'Data', 1, align='C', fill=True)
                pdf.ln()
            
            def vazio(pdf):
                pdf.cell(188, 4, "", border=1) 
                pdf.ln()

            def totais(valor, recebido=None):
                pdf.set_font('Arial', size=9)
                pdf.cell(145, 10, txt=f'{valor} Registro(s)')
                if recebido is not None:
                    pdf.cell(200, 10, txt=f'Total R$ {recebido}')
                pdf.ln(7)

            if processos_filtrados:

                if filtro_execucao:
                    cabecalhoExecucao(pdf)

                    executados = 0
                    total_credito = []

                    for processo in processos_filtrados:
                        status_list = []
                        
                        if processo.ativo == True:
                            andamentos_do_processo = processo.andamento_set.filter(ativo=True)
                            for andamento in andamentos_do_processo:                  
                                if andamento.tipo_andamento.status == 'Executado':
                                    status_list.append('Executado')

                            if andamentos_do_processo:
                                maior_data = andamentos_do_processo.aggregate(max_data=Max('data_andamento'))['max_data']
                                maior_data = str(maior_data)
                                andamentos_maior_data = andamentos_do_processo.filter(data_andamento=maior_data)
                                maior_sequencial = andamentos_maior_data.aggregate(max_sequencial=Max('sequencial'))['max_sequencial']
                                ultimo_andamento = andamentos_maior_data.get(sequencial=maior_sequencial)
                                if str(ultimo_andamento.tipo_andamento).upper() == 'FIM DO CONTRATO COM A ASSESSORIA - 39':
                                    penultimo = andamentos_maior_data.filter(sequencial__lt=maior_sequencial).order_by('-sequencial').first() 
                                    if penultimo is not None:
                                        ultimo_andamento = penultimo
                                    else:
                                        ultimo_andamento = ultimo_andamento
                                
                                if str(ultimo_andamento.tipo_andamento).upper() != 'ENCERRADO - 36':
                                    if 'Executado' in status_list:
                                        executados += 1

                                        if processo.valor_atualizado:
                                            total_credito.append(processo.valor_atualizado)
                                            valor_credito = processo.valor_atualizado
                                            valor_credito = '{:,.2f}'.format(valor_credito).replace(',', 'X').replace('.', ',').replace('X', '.') 

                                        elif processo.valor_credito:
                                            total_credito.append(processo.valor_credito)
                                            valor_credito = processo.valor_credito
                                            valor_credito = '{:,.2f}'.format(valor_credito).replace(',', 'X').replace('.', ',').replace('X', '.') 
                                        else:
                                            valor_credito = '0,00'

                                        data_andamento = str(ultimo_andamento.data_andamento).split('-')
                                        ano, mes, dia = data_andamento
                                        data_andamento_convertida = f'{dia}/{mes}/{ano}'

                                        if len(str(processo.numero)) > 4:
                                            numero_processo = f'{str(processo.numero)[:-4]}/{str(processo.numero)[-4:]}'

                                        else:
                                            numero_processo = processo.numero

                                        pdf.set_font('Arial', size=9)
                                        pdf.cell(115, 4, str(processo.contribuinte.nome_contribuinte[:49]), 1, align='L') 
                                        pdf.cell(22, 4, str(numero_processo), 1, align='R')
                                        pdf.cell(31, 4, str(valor_credito), 1, align='R')
                                        pdf.cell(20, 4, str(data_andamento_convertida), 1, align='C')
                                        pdf.ln()

                    if executados == 0:
                        vazio(pdf)

                    total_credito_execucao = sum(total_credito)
                    total_credito_execucao = '{:,.2f}'.format(total_credito_execucao).replace(',', 'X').replace('.', ',').replace('X', '.') 

                    totais(executados, total_credito_execucao)

                # # # -------------------------------------------------------------------------------
                # # PROCESSOS - STATUS RECEBIDOS
                def cabecalhoRecebidos(pdf):
                    pdf.set_font('Arial', 'B', size=12)
                    pdf.cell(200, 10, 'Processos Recebidos', align='C')
                    pdf.ln(10)

                    pdf.set_font('Arial', 'B', size=10)
                    pdf.set_draw_color(0, 0, 0) 
                    pdf.set_line_width(0.3)   

                    pdf.set_fill_color(211,211,211) 
                    pdf.cell(115, 5, 'Empresa', 1, align='C', fill=True)
                    pdf.cell(22, 5, 'Processo', 1, align='C', fill=True)
                    pdf.cell(31, 5, 'Pago', 1, align='C', fill=True)
                    pdf.cell(20, 5, 'Data', 1, align='C', fill=True)
                    pdf.ln()

                if filtro_recebido:
                    cabecalhoRecebidos(pdf)
        
                    total_pago = 0
                    recebidos = 0

                    for processo in processos_filtrados:
                        if processo.ativo == True:

                            andamentos_do_processo = processo.andamento_set.filter(ativo=True)

                            lista_recebidos = []
                            total_valor_pago_recebidos = 0
                            for andamento in andamentos_do_processo:
                                if andamento.valor_pago != 0:
                                    lista_recebidos.append(andamento)

                                try:
                                    avaliacao = Avaliacao.objects.get(andamento_id=andamento.id)
                                except:
                                    avaliacao = None
                                if avaliacao is not None and avaliacao.valor_pago_avaliacao != 0:
                                    lista_recebidos.append(andamento)
            
                            if len(lista_recebidos) == 1:
                                recebidos += 1
                                andamento = lista_recebidos[0]

                                if str(andamento.tipo_andamento) == 'Avaliação Imobiliária - 05':
                                    avaliacao = Avaliacao.objects.get(andamento_id=andamento.id)
                                    if avaliacao.valor_pago_avaliacao:
                                        total_pago += avaliacao.valor_pago_avaliacao
                                        valor_pago = avaliacao.valor_pago_avaliacao
                                        if valor_pago:
                                            valor_pago = '{:,.2f}'.format(valor_pago).replace(',', 'X').replace('.', ',').replace('X', '.') 
                                    if avaliacao.data_valor_pago:
                                        data_andamento = str(avaliacao.data_valor_pago).split('-')
                                        ano, mes, dia = data_andamento 
                                        data_andamento_convertida = f'{dia}/{mes}/{ano}'
                                    else:
                                        data_andamento_convertida = ''
                                else:
                                    if andamento.valor_pago:
                                        total_pago += andamento.valor_pago
                                    valor_pago = andamento.valor_pago
                                    if valor_pago:
                                        valor_pago = '{:,.2f}'.format(valor_pago).replace(',', 'X').replace('.', ',').replace('X', '.') 
                                    data_andamento = str(andamento.data_andamento).split('-')
                                    ano, mes, dia = data_andamento
                                    data_andamento_convertida = f'{dia}/{mes}/{ano}'

                                if len(str(processo.numero)) > 4:
                                    numero_processo = f'{str(processo.numero)[:-4]}/{str(processo.numero)[-4:]}'
                                else:
                                    numero_processo = processo.numero

                                pdf.set_font('Arial', size=9)
                                pdf.cell(115, 4, str(processo.contribuinte.nome_contribuinte[:49]), 1, align='L')
                                pdf.cell(22, 4, str(numero_processo), 1, align='R')
                                pdf.cell(31, 4, str(valor_pago), 1, align='R')
                                pdf.cell(20, 4, str(data_andamento_convertida), 1, align='C')
                                pdf.ln()

                            elif len(lista_recebidos) > 1:
                                recebidos += 1
                                for andamento in lista_recebidos:
                                    if str(andamento.tipo_andamento) == 'Avaliação Imobiliária - 05':
                                        avaliacao = Avaliacao.objects.get(andamento_id=andamento.id)
                                        if avaliacao.valor_pago_avaliacao:
                                            total_valor_pago_recebidos += avaliacao.valor_pago_avaliacao
                                            total_pago += avaliacao.valor_pago_avaliacao
                                    else:
                                        if andamento.valor_pago:
                                            total_valor_pago_recebidos += andamento.valor_pago
                                            total_pago += andamento.valor_pago

                                maior_data = None
                                maior_sequencial = None
                                ultimo_andamento_recebido = None
                                for andamento in lista_recebidos:
                                    if maior_data is None or andamento.data_andamento > maior_data:
                                        maior_data = andamento.data_andamento
                                        maior_sequencial = andamento.sequencial
                                        ultimo_andamento_recebido = andamento
                                    elif andamento.data_andamento == maior_data and (maior_sequencial is None or andamento.sequencial > maior_sequencial):
                                        maior_sequencial = andamento.sequencial
                                        ultimo_andamento_recebido = andamento

                                if str(ultimo_andamento_recebido.tipo_andamento) == 'Avaliação Imobiliária - 05':
                                    avaliacao = Avaliacao.objects.get(andamento_id=ultimo_andamento_recebido.id)
                                    if avaliacao.data_valor_pago:
                                        data_andamento = str(avaliacao.data_valor_pago).split('-')
                                        ano, mes, dia = data_andamento 
                                        data_andamento_convertida = f'{dia}/{mes}/{ano}'
                                    else:
                                        data_andamento = str(ultimo_andamento_recebido.data_andamento).split('-')
                                        ano, mes, dia = data_andamento 
                                        data_andamento_convertida = f'{dia}/{mes}/{ano}'
                                else:
                                    data_andamento = str(ultimo_andamento_recebido.data_andamento).split('-')
                                    ano, mes, dia = data_andamento 
                                    data_andamento_convertida = f'{dia}/{mes}/{ano}'

                                valor_pago = total_valor_pago_recebidos
                                valor_pago = '{:,.2f}'.format(valor_pago).replace(',', 'X').replace('.', ',').replace('X', '.') 

                                if len(str(processo.numero)) > 4:
                                    numero_processo = f'{str(processo.numero)[:-4]}/{str(processo.numero)[-4:]}'
                                else:
                                    numero_processo = processo.numero

                                pdf.set_font('Arial', size=9)
                                pdf.cell(115, 4, str(processo.contribuinte.nome_contribuinte[:49]), 1, align='L')
                                pdf.cell(22, 4, str(numero_processo), 1, align='R')
                                pdf.cell(31, 4, str(valor_pago), 1, align='R')
                                pdf.cell(20, 4, str(data_andamento_convertida), 1, align='C')
                                pdf.ln()
                            
                    if recebidos == 0:
                        vazio(pdf)

                    total_valor_recebido = total_pago
                    total_valor_recebido = '{:,.2f}'.format(total_valor_recebido).replace(',', 'X').replace('.', ',').replace('X', '.')

                    totais(recebidos, total_valor_recebido)
                # # # -------------------------------------------------------------------------------
                
                # #  PROCESSOS - STATUS EM ANDAMENTO
                def cabecalhoAndamento(pdf):
                    pdf.set_font('Arial', 'B', size=12)
                    pdf.cell(200, 10, 'Processos Em Andamento', align='C')
                    pdf.ln(10)

                    pdf.set_font('Arial', 'B', size=10) 
                    pdf.set_draw_color(0, 0, 0) 
                    pdf.set_line_width(0.3) 

                    if filtro_colunas:
                        pdf.set_fill_color(211, 211, 211)
                        pdf.cell(82, 5, 'Empresa', 1, align='C', fill=True)
                        pdf.cell(22, 5, 'Processo', 1, align='C', fill=True)
                        pdf.cell(18, 5, 'Data', 1, align='C', fill=True)
                        pdf.cell(66, 5, 'Tipo Andamento', 1, align='C', fill=True)
                        pdf.ln()
                    else:
                        pdf.set_fill_color(211, 211, 211) 
                        pdf.cell(166, 5, 'Empresa', 1, align='C', fill=True)
                        pdf.cell(22, 5, 'Processo', 1, align='C', fill=True)
                        pdf.ln()
                    
                if filtro_andamento:
                    cabecalhoAndamento(pdf)

                    em_andamento = 0

                    for processo in processos_filtrados:
                        if processo.ativo == True:
                            andamentos_do_processo = processo.andamento_set.filter(ativo=True)
                            if andamentos_do_processo:
                                maior_data = andamentos_do_processo.aggregate(max_data=Max('data_andamento'))['max_data']
                                maior_data = str(maior_data)
                                andamentos_maior_data = andamentos_do_processo.filter(data_andamento=maior_data)
                                maior_sequencial = andamentos_maior_data.aggregate(max_sequencial=Max('sequencial'))['max_sequencial']
                                ultimo_andamento = andamentos_maior_data.get(sequencial=maior_sequencial)
                                            
                                if str(ultimo_andamento.tipo_andamento).upper() == 'FIM DO CONTRATO COM A ASSESSORIA - 39':
                                    if len(andamentos_do_processo) == 1:
                                        ultimo_andamento = ultimo_andamento

                                    elif len(andamentos_maior_data) > 1:
                                        penultimo_andamento = andamentos_maior_data.filter(sequencial__lt=maior_sequencial).order_by('-sequencial').first()

                                        if penultimo_andamento:
                                            if str(penultimo_andamento.tipo_andamento.status) == 'Em Andamento':
                                                ultimo_andamento = ultimo_andamento
                                            else:
                                                ultimo_andamento = penultimo_andamento

                                    else:
                                        andamentos_segunda_maior_data = andamentos_do_processo.filter(data_andamento__lt=maior_data) 
                                        if andamentos_segunda_maior_data.exists(): 
                                            maior_seq = andamentos_segunda_maior_data.aggregate(max_sequencial=Max('sequencial'))['max_sequencial']
                                            penultimo_andamento = andamentos_segunda_maior_data.get(sequencial=maior_seq)

                                        if penultimo_andamento:
                                            if str(penultimo_andamento.tipo_andamento.status) == 'Em Andamento':
                                                ultimo_andamento = ultimo_andamento
                                            else:
                                                ultimo_andamento = penultimo_andamento

                                if ultimo_andamento.tipo_andamento.status == 'Em Andamento':
                                    data_andamento = str(ultimo_andamento.data_andamento).split("-")
                                    ano, mes, dia = data_andamento 
                                    data_andamento_convertida = f'{dia}/{mes}/{ano}'

                                    tipo_andamento = str(ultimo_andamento.tipo_andamento)
                                    em_andamento += 1

                                    if len(str(processo.numero)) > 4:
                                        numero_processo = f'{str(processo.numero)[:-4]}/{str(processo.numero)[-4:]}'
                                    else:
                                        numero_processo = processo.numero

                                    if filtro_colunas:
                                        pdf.set_font('Arial', size=9)
                                        pdf.cell(82, 4, str(processo.contribuinte.nome_contribuinte[:36]), 1, align='L')
                                        pdf.cell(22, 4, str(numero_processo), 1, align='R')
                                        pdf.cell(18, 4, str(data_andamento_convertida), 1, align='C')
                                        pdf.cell(66, 4, str(tipo_andamento[:-4]), 1, align='L')
                                        pdf.ln()
                                    else:
                                        pdf.set_font('Arial', size=9)
                                        pdf.cell(166, 4, str(processo.contribuinte.nome_contribuinte[:70]), 1, align='L')
                                        pdf.cell(22, 4, str(numero_processo), 1, align='R')
                                        pdf.ln()

                    if  em_andamento == 0:
                        vazio(pdf)

                    totais(em_andamento)

                # # # # -------------------------------------------------------------------------------
                # #  PROCESSOS - STATUS ENCERRADOS
                def cabecalhoEncerrados(pdf): 
                    pdf.set_font('Arial', 'B', size=12)
                    pdf.cell(200, 10, 'Processos Encerrados', align='C')
                    pdf.ln(10)

                    pdf.set_font('Arial', 'B', size=10) 
                    pdf.set_draw_color(0, 0, 0) 
                    pdf.set_line_width(0.3)    

                    pdf.set_fill_color(211, 211, 211) 
                    pdf.cell(146, 5, 'Empresa', 1, align='C', fill=True)
                    pdf.cell(22, 5, 'Processo', 1, align='C', fill=True)
                    pdf.cell(20, 5, 'Data', 1, align='C', fill=True)
                    pdf.ln()

                if filtro_encerrado:
                    cabecalhoEncerrados(pdf)

                    encerrados = 0

                    for processo in processos_filtrados:
                        if processo.ativo == True:
                            andamentos_do_processo = processo.andamento_set.filter(ativo=True)
                            if andamentos_do_processo:
                                maior_data = andamentos_do_processo.aggregate(max_data=Max('data_andamento'))['max_data']
                                maior_data = str(maior_data)
                                andamentos_maior_data = andamentos_do_processo.filter(data_andamento=maior_data)
                                maior_sequencial = andamentos_maior_data.aggregate(max_sequencial=Max('sequencial'))['max_sequencial']
                                ultimo_andamento = andamentos_maior_data.get(sequencial=maior_sequencial)
                                if str(ultimo_andamento.tipo_andamento).upper() == 'FIM DO CONTRATO COM A ASSESSORIA - 39':
                                    if len(andamentos_maior_data) > 1:
                                        penultimo_andamento = andamentos_maior_data.filter(sequencial__lt=maior_sequencial).order_by('-sequencial').first() 
                                        if penultimo_andamento:
                                            ultimo_andamento = penultimo_andamento
                                    else:
                                        andamentos_segunda_maior_data = andamentos_do_processo.filter(data_andamento__lt=maior_data) 
                                        if andamentos_segunda_maior_data.exists():
                                            maior_seq = andamentos_segunda_maior_data.aggregate(max_sequencial=Max('sequencial'))['max_sequencial']
                                            penultimo_andamento = andamentos_segunda_maior_data.get(sequencial=maior_seq)
                                            if penultimo_andamento:
                                                ultimo_andamento = penultimo_andamento
                                
                                if ultimo_andamento.tipo_andamento.status == 'Encerrado':
                                    encerrados += 1
                                    data_andamento = str(ultimo_andamento.data_andamento).split('-')
                                    ano, mes, dia = data_andamento
                                    data_andamento_convertida = f'{dia}/{mes}/{ano}'

                                    if len(str(processo.numero)) > 4:
                                        numero_processo = f'{str(processo.numero)[:-4]}/{str(processo.numero)[-4:]}'
                                    else:
                                        numero_processo = processo.numero

                                    pdf.set_font('Arial', size=9)
                                    pdf.cell(146, 4, str(processo.contribuinte.nome_contribuinte[:62]), 1, align='L')
                                    pdf.cell(22, 4, str(numero_processo), 1, align='R')
                                    pdf.cell(20, 4, str(data_andamento_convertida), 1, align='C')
                                    pdf.ln()

                    if encerrados == 0:
                        vazio(pdf)

                    totais(encerrados)

                temp_file = tempfile.NamedTemporaryFile(delete=False)
                pdf.output(temp_file.name)
                temp_file.close()

                with open(temp_file.name, 'rb') as file:
                    pdf_content = file.read()
            
                os.unlink(temp_file.name)

                response = HttpResponse(pdf_content, content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="processos_por_municipio.pdf"'

                return response

            else:
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                pdf.output(temp_file.name)
                temp_file.close()

                with open(temp_file.name, 'rb') as file:
                    pdf_content = file.read()
            
                os.unlink(temp_file.name)

                response = HttpResponse(pdf_content, content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="processos_por_municipio.pdf"'

                return response
                
        except Exception as error:
            print(f'Error na funcao (get) - views: (RelatorioProcessosPorStatus) - error: {str(error)}')
        
class RelatorioAvaliacoes(LoginRequiredMixin, View):
    """
        Relatório de Avaliações "Avaliações"
    """
    model = Avaliacao

    def get(self, request, *args, **kwargs):
        try:
            usuario_gerou = self.request.user
                        
            data_atual = datetime.now()
            data_gerou = data_atual - timedelta(hours=1) 
            data_gerou = data_gerou.strftime("%d/%m/%Y %H:%M:%S")
            
            filtro_modelo = request.GET.get('modelo')
            filtro_municipio = request.GET.get('municipio2')
            filtro_data_ava_ini = request.GET.get('data_ini')
            filtro_data_ava_fin = request.GET.get('data_fin')
            filtro_andamento_avaliacao = request.GET.get('andamento_avaliacao_tipo')

            if filtro_andamento_avaliacao:
                get_andamento_aval = TipoAndamentoAvaliacao.objects.get(id=int(filtro_andamento_avaliacao))
                andamento_aval = f'Andamento: {get_andamento_aval}' 
            else:
                andamento_aval = ''

            if filtro_data_ava_ini:
                header_data_ini = str(filtro_data_ava_ini).split('-')
                ano, mes, dia = header_data_ini 
                header_data_ini = f'{dia}/{mes}/{ano}'
            if filtro_data_ava_fin:
                header_data_fin = str(filtro_data_ava_fin).split('-')
                ano, mes, dia = header_data_fin 
                header_data_fin = f'{dia}/{mes}/{ano}'

            if filtro_data_ava_ini and filtro_data_ava_fin:
                periodo = f'Data da avaliação: De {header_data_ini} até {header_data_fin}'
            elif filtro_data_ava_ini:
                periodo = f'Data da avaliação: De {header_data_ini} até {header_data_ini}'
            elif filtro_data_ava_fin:
                periodo = f'Data da avaliação: De {header_data_ini} até {header_data_ini}'
            else:
                periodo = ''          

            if filtro_municipio:
                get_municipio = Municipio.objects.get(id=filtro_municipio)
                nome_municipio = get_municipio.nome
            else:
                nome_municipio = ''

            x_nome_empresa = 270
            y_nome_empresa = -5
            x_titulo_rel = 270
            y_titulo_rel = 15
            x_periodo = 270
            y_periodo = 0
            x_andamento = 270
            y_andamento = 0

            if filtro_modelo == '':
                titulo_relatorio = 'Relatório de Avaliações - Com Último Andamento do Município de '
            elif filtro_modelo == '1':
                titulo_relatorio = 'Relatório de Avaliações - Incremento de ITBI Apurado do Município de'
            elif filtro_modelo == '2':
                titulo_relatorio = 'Relatório de Avaliações - Incremento de ITBI Pago do Município de'
            else:
                titulo_relatorio = ''
            
            pdf = Estrutura_Pdf(titulo_relatorio, x_nome_empresa, y_nome_empresa, x_titulo_rel, y_titulo_rel, usuario_gerou, data_gerou, nome_municipio, periodo, x_periodo, y_periodo, andamento_aval, x_andamento, y_andamento) 
            pdf.add_page(orientation='L')  

            pdf.set_font('Arial', 'B', size=7) 
            pdf.set_draw_color(0, 0, 0) 
            pdf.set_line_width(0.3)  
            
            if filtro_modelo == '': 
                """
                    # RELATÓRIO - AVALIAÇÃO COM ÚLTIMO ANDAMENTO
                """

                pdf.set_fill_color(211,211,211) 
                pdf.cell(65 * 0.7, 4, 'Contribuinte', 1, align='C', fill=True) 
                pdf.cell(20 * 0.7, 4, 'Processo', 1, align='C', fill=True) 
                pdf.cell(20 * 0.7, 4, 'Finalidade', 1, align='C', fill=True)
                pdf.cell(21 * 0.7, 4, 'Área', 1, align='C', fill=True)
                pdf.cell(56 * 0.7, 4, 'Operação', 1, align='C', fill=True)
                pdf.cell(29 * 0.7, 4, 'Valor Declarado', 1, align='C', fill=True)
                pdf.cell(29 * 0.7, 4, 'Valor Avaliado', 1, align='C', fill=True)
                pdf.cell(29 * 0.7, 4, 'ITBI Apurado', 1, align='C', fill=True)
                pdf.cell(29 * 0.7, 4, 'ITBI Pago', 1, align='C', fill=True)
                pdf.cell(31 * 0.7, 4, 'Data Pagamento', 1, align='C', fill=True)
                pdf.cell(65 * 0.7, 4, 'Situação', 1, align='C', fill=True)
                pdf.ln()

                if filtro_municipio:
                    processos_filtrados = Processo.objects.filter(municipio_id=filtro_municipio, ativo=True).order_by('contribuinte__nome_contribuinte') 
            
                    tot_registros = 0
                    tot_val_declarado = 0
                    tot_val_avaliado = 0
                    tot_itbi_apurado = 0
                    tot_itbi_pago = 0
                    
                    for processo in processos_filtrados:
                        if len(str(processo.numero)) > 4:
                            numero_processo = f'{str(processo.numero)[:-4]}/{str(processo.numero)[-4:]}'
                        else:
                            numero_processo = processo.numero

                        andamentos_do_processo = processo.andamento_set.filter(ativo=True)
                        if andamentos_do_processo:
                            maior_data = andamentos_do_processo.aggregate(max_data=Max('data_andamento'))['max_data']
                            maior_data = str(maior_data)
                            andamentos_maior_data = andamentos_do_processo.filter(data_andamento=maior_data)
                            maior_sequencial = andamentos_maior_data.aggregate(max_sequencial=Max('sequencial'))['max_sequencial'] 
                            ultimo_andamento = andamentos_maior_data.get(sequencial=maior_sequencial)
                        else:
                            ultimo_andamento = '' 

                        if ultimo_andamento != '':
                            tipo_andamento = ultimo_andamento.tipo_andamento
                            tipo_andamento = str(tipo_andamento)


                        avaliacoes_filtradas = Avaliacao.objects.filter(andamento__processo=processo, ativo=True).order_by('sequencial')

                        if filtro_data_ava_ini and filtro_data_ava_fin:
                            if filtro_data_ava_ini != filtro_data_ava_fin:
                                avaliacoes_filtradas = avaliacoes_filtradas.filter(data_avaliacao__range=(filtro_data_ava_ini, filtro_data_ava_fin))
                            else:
                                avaliacoes_filtradas = avaliacoes_filtradas.filter(data_avaliacao=filtro_data_ava_ini)
                        elif filtro_data_ava_ini:
                            avaliacoes_filtradas = avaliacoes_filtradas.filter(data_avaliacao=filtro_data_ava_ini)
                        elif filtro_data_ava_fin:
                            avaliacoes_filtradas = avaliacoes_filtradas.filter(data_avaliacao=filtro_data_ava_fin)
                        
                        if filtro_andamento_avaliacao:
                            avaliacoes_filtradas = avaliacoes_filtradas.filter(tipo_andamento_avaliacao=filtro_andamento_avaliacao)

                        if avaliacoes_filtradas:
                            for avaliacao in avaliacoes_filtradas:
                                tot_registros += 1
                                
                                if avaliacao.finalidade:
                                    finalidade = avaliacao.finalidade
                                else:
                                    finalidade = '-'

                                if avaliacao.area:
                                    if str(avaliacao.finalidade) == 'Urbano':
                                        area = round(avaliacao.area, 2) 
                                    else:
                                        area = avaliacao.area
                                else:
                                    area = '-'

                                if avaliacao.operacao:
                                    operacao = avaliacao.operacao
                                else:
                                    operacao = '-'

                                if avaliacao.valor_declarado:
                                    tot_val_declarado += avaliacao.valor_declarado
                                    valor_declarado = '{:,.2f}'.format(avaliacao.valor_declarado).replace(',', 'X').replace('.', ',').replace('X', '.')
                                else:
                                    valor_declarado = '-'

                                if avaliacao.valor_avaliado:
                                    tot_val_avaliado += avaliacao.valor_avaliado
                                    valor_avaliado = '{:,.2f}'.format(avaliacao.valor_avaliado).replace(',', 'X').replace('.', ',').replace('X', '.')
                                else:
                                    valor_avaliado = '-'

                                if avaliacao.valor_itbi_diferenca and avaliacao.valor_itbi_diferenca > 0:
                                    tot_itbi_apurado += avaliacao.valor_itbi_diferenca
                                    valor_itbi_diferenca = '{:,.2f}'.format(avaliacao.valor_itbi_diferenca).replace(',', 'X').replace('.', ',').replace('X', '.')   
                                else:
                                    valor_itbi_diferenca = '-'

                                if avaliacao.valor_pago_avaliacao:
                                    tot_itbi_pago += avaliacao.valor_pago_avaliacao
                                    valor_itbi_pago = '{:,.2f}'.format(avaliacao.valor_pago_avaliacao).replace(',', 'X').replace('.', ',').replace('X', '.')                  
                                else:
                                    valor_itbi_pago = '-'

                                if avaliacao.data_valor_pago:
                                    data_valor_pago = str(avaliacao.data_valor_pago).split('-')
                                    ano, mes, dia = data_valor_pago 
                                    data_valor_pago = f'{dia}/{mes}/{ano}'
                                else:
                                    data_valor_pago = '-'  

                                pdf.set_font('Arial', size=6)
                                pdf.cell(65 * 0.7, 4, str(processo.contribuinte.nome_contribuinte[:32]), 1, align='L')
                                pdf.cell(20 * 0.7, 4, str(numero_processo), 1, align='R')
                                pdf.cell(20 * 0.7, 4, str(finalidade), 1, align='R')
                                pdf.cell(21 * 0.7, 4, str(area), 1, align='R')
                                pdf.cell(56 * 0.7, 4, str(operacao), 1, align='C')
                                pdf.cell(29 * 0.7, 4, str(valor_declarado), 1, align='R')
                                pdf.cell(29 * 0.7, 4, str(valor_avaliado), 1, align='R')
                                pdf.cell(29 * 0.7, 4, str(valor_itbi_diferenca), 1, align='R')
                                pdf.cell(29 * 0.7, 4, str(valor_itbi_pago), 1, align='R')
                                pdf.cell(31 * 0.7, 4, str(data_valor_pago), 1, align='R')
                                pdf.cell(65 * 0.7, 4, str(tipo_andamento[:-4]), 1, align='L')
                                pdf.ln()
                    
                    tot_val_declarado = '{:,.2f}'.format(tot_val_declarado).replace(',', 'X').replace('.', ',').replace('X', '.')
                    tot_val_avaliado = '{:,.2f}'.format(tot_val_avaliado).replace(',', 'X').replace('.', ',').replace('X', '.')
                    tot_itbi_apurado = '{:,.2f}'.format(tot_itbi_apurado).replace(',', 'X').replace('.', ',').replace('X', '.')
                    tot_itbi_pago = '{:,.2f}'.format(tot_itbi_pago).replace(',', 'X').replace('.', ',').replace('X', '.')

                    pdf.set_font('Arial', size=6)
                    pdf.cell(145, 5, txt=f'{tot_registros} Registro(s)')
                    pdf.cell(3, 5, txt=f'R$ {tot_val_declarado}', align='R')
                    pdf.cell(21, 5, txt=f'R$ {tot_val_avaliado}', align='R')
                    pdf.cell(20, 5, txt=f'R$ {tot_itbi_apurado}', align='R')
                    pdf.cell(20, 5, txt=f'R$ {tot_itbi_pago}', align='R')
                    pdf.ln(2) 

                    temp_file = tempfile.NamedTemporaryFile(delete=False)
                    pdf.output(temp_file.name)
                    temp_file.close()

                    with open(temp_file.name, 'rb') as file:
                        pdf_content = file.read()
                    
                    os.unlink(temp_file.name)

                    response = HttpResponse(pdf_content, content_type='application/pdf')
                    response['Content-Disposition'] = 'inline; filename="avaliacoes.pdf"' 

                    return response

                else:
                    temp_file = tempfile.NamedTemporaryFile(delete=False)
                    pdf.output(temp_file.name)
                    temp_file.close()

                    with open(temp_file.name, 'rb') as file:
                        pdf_content = file.read()
                    
                    os.unlink(temp_file.name)

                    response = HttpResponse(pdf_content, content_type='application/pdf')
                    response['Content-Disposition'] = 'inline; filename="avaliacoes.pdf"' 

                    return response

            elif filtro_modelo == '1':
                """
                    # RELATÓRIO - INCREMENTO DE ITBI APURADO
                """

                pdf.set_fill_color(211,211,211) 
                pdf.cell(98 * 0.7, 4, 'Contribuinte', 1, align='C', fill=True) 
                pdf.cell(18 * 0.7, 4, 'Processo', 1, align='C', fill=True) 
                pdf.cell(27 * 0.7, 4, 'Matrícula', 1, align='C', fill=True)
                pdf.cell(20 * 0.7, 4, 'Finalidade', 1, align='C', fill=True)
                pdf.cell(19 * 0.7, 4, 'Área', 1, align='C', fill=True)
                pdf.cell(48 * 0.7, 4, 'Operação', 1, align='C', fill=True)
                pdf.cell(27 * 0.7, 4, 'Val. Declarado', 1, align='C', fill=True)
                pdf.cell(27 * 0.7, 4, 'ITBI Declarado', 1, align='C', fill=True)
                pdf.cell(27 * 0.7, 4, 'Val. Avaliado', 1, align='C', fill=True)
                pdf.cell(27 * 0.7, 4, 'ITBI Apurado', 1, align='C', fill=True)
                pdf.cell(27 * 0.7, 4, 'ITBI Pago', 1, align='C', fill=True)
                pdf.cell(29 * 0.7, 4, 'Incremento ITBI', 1, align='C', fill=True)
                pdf.ln()

                if filtro_municipio:
                    processos_filtrados = Processo.objects.filter(municipio_id=filtro_municipio, ativo=True).order_by('contribuinte__nome_contribuinte') 
                    
                    tot_registros = 0
                    tot_val_declarado = 0
                    tot_val_avaliado = 0
                    tot_itbi_apurado = 0
                    tot_itbi_pago = 0
                    tot_itbi_declarado = 0
                    tot_incremento_itbi = 0
                    
                    for processo in processos_filtrados:
                        if len(str(processo.numero)) > 4:
                            numero_processo = f'{str(processo.numero)[:-4]}/{str(processo.numero)[-4:]}'
                        else:
                            numero_processo = processo.numero

                        avaliacoes_filtradas = Avaliacao.objects.filter(andamento__processo=processo, ativo=True).order_by('sequencial')

                        if filtro_data_ava_ini and filtro_data_ava_fin:
                            if filtro_data_ava_ini != filtro_data_ava_fin:
                                avaliacoes_filtradas = avaliacoes_filtradas.filter(data_avaliacao__range=(filtro_data_ava_ini, filtro_data_ava_fin))
                            else:
                                avaliacoes_filtradas = avaliacoes_filtradas.filter(data_avaliacao=filtro_data_ava_ini)
                        elif filtro_data_ava_ini:
                            avaliacoes_filtradas = avaliacoes_filtradas.filter(data_avaliacao=filtro_data_ava_ini)
                        elif filtro_data_ava_fin:
                            avaliacoes_filtradas = avaliacoes_filtradas.filter(data_avaliacao=filtro_data_ava_fin)
                        
                        if filtro_andamento_avaliacao:
                            avaliacoes_filtradas = avaliacoes_filtradas.filter(tipo_andamento_avaliacao=filtro_andamento_avaliacao)

                        if avaliacoes_filtradas:
                            for avaliacao in avaliacoes_filtradas:
                                tot_registros += 1
                                
                                if avaliacao.finalidade:
                                    finalidade = avaliacao.finalidade
                                else:
                                    finalidade = '-'

                                if avaliacao.area:
                                    if str(avaliacao.finalidade) == 'Urbano':
                                        area = round(avaliacao.area, 2)
                                    else:
                                        area = avaliacao.area
                                else:
                                    area = '-'

                                if avaliacao.operacao:
                                    operacao = avaliacao.operacao
                                else:
                                    operacao = '-'

                                if avaliacao.valor_declarado and avaliacao.valor_declarado > 0:
                                    tot_val_declarado += avaliacao.valor_declarado
                                    valor_declarado = '{:,.2f}'.format(avaliacao.valor_declarado).replace(',', 'X').replace('.', ',').replace('X', '.')
                                else:
                                    valor_declarado = '-'

                                if avaliacao.valor_avaliado and avaliacao.valor_avaliado > 0:
                                    tot_val_avaliado += avaliacao.valor_avaliado
                                    valor_avaliado = '{:,.2f}'.format(avaliacao.valor_avaliado).replace(',', 'X').replace('.', ',').replace('X', '.')
                                else:
                                    valor_avaliado = '-'

                                if avaliacao.valor_itbi_diferenca and avaliacao.valor_itbi_diferenca > 0:
                                    tot_itbi_apurado += avaliacao.valor_itbi_diferenca
                                    valor_itbi_diferenca = '{:,.2f}'.format(avaliacao.valor_itbi_diferenca).replace(',', 'X').replace('.', ',').replace('X', '.')   
                                else:
                                    valor_itbi_diferenca = '-'

                                if avaliacao.valor_pago_avaliacao and avaliacao.valor_pago_avaliacao > 0:
                                    tot_itbi_pago += avaliacao.valor_pago_avaliacao
                                    valor_itbi_pago = '{:,.2f}'.format(avaliacao.valor_pago_avaliacao).replace(',', 'X').replace('.', ',').replace('X', '.')                  
                                else:
                                    valor_itbi_pago = '-'

                                if avaliacao.valor_declarado:

                                    operacao_id = avaliacao.operacao.id

                                    """
                                        IDs: 5 - INTEGRALIZAÇÃO / INCORPORAÇÃO | 6 - CISÃO | 7 - FUSÃO | 8 - EXTINÇÃO DE CONDOMÍNIO | 9 - EXTINÇÃO DE PESSOA JURÍDICA
                                    """
                                    if operacao_id == 5 or operacao_id == 6 or operacao_id == 7 or operacao_id == 8 or operacao_id == 9:
                                        itbi_declarado = '-'
                                    else:
                                        itbi_declarado = avaliacao.valor_declarado * 2/100
                                        if itbi_declarado > 0:
                                            tot_itbi_declarado += itbi_declarado
                                            itbi_declarado = '{:,.2f}'.format(itbi_declarado).replace(',', 'X').replace('.', ',').replace('X', '.') 
                                        else:
                                            itbi_declarado = '-'
                                else:
                                    itbi_declarado = '-'

                                if avaliacao.valor_itbi_diferenca and avaliacao.valor_declarado:
                                    calc_itbi_declarado = avaliacao.valor_declarado * 2/100
                                    incremento_itbi = avaliacao.valor_itbi_diferenca - calc_itbi_declarado
                                    if incremento_itbi > 0:
                                        operacao_id = avaliacao.operacao.id
                                        if operacao_id == 5 or operacao_id == 6 or operacao_id == 7 or operacao_id == 8 or operacao_id == 9:
                                            incremento_itbi = valor_itbi_pago
                                        else:
                                            tot_incremento_itbi += incremento_itbi
                                            incremento_itbi = '{:,.2f}'.format(incremento_itbi).replace(',', 'X').replace('.', ',').replace('X', '.')
                                    else:
                                        incremento_itbi = '-'
                                else:
                                    incremento_itbi = '-'

                                pdf.set_font('Calibri', 'B', size=6)
                                pdf.cell(98 * 0.7, 4, str(processo.contribuinte.nome_contribuinte[:55]), 1, align='L')
                                pdf.cell(18 * 0.7, 4, str(numero_processo), 1, align='R')
                                pdf.cell(27 * 0.7, 4, str(avaliacao.matricula), 1, align='R')
                                pdf.cell(20 * 0.7, 4, str(finalidade), 1, align='C')
                                pdf.cell(19 * 0.7, 4, str(area), 1, align='R')
                                pdf.cell(48 * 0.7, 4, str(operacao), 1, align='C')
                                pdf.cell(27 * 0.7, 4, str(valor_declarado), 1, align='R')
                                pdf.cell(27 * 0.7, 4, str(itbi_declarado), 1, align='R')
                                pdf.cell(27 * 0.7, 4, str(valor_avaliado), 1, align='R')
                                pdf.cell(27 * 0.7, 4, str(valor_itbi_diferenca), 1, align='R')
                                pdf.cell(27 * 0.7, 4, str(valor_itbi_pago), 1, align='R')
                                pdf.cell(29 * 0.7, 4, str(incremento_itbi), 1, align='R')

                                pdf.ln()

                    tot_val_declarado = '{:,.2f}'.format(tot_val_declarado).replace(',', 'X').replace('.', ',').replace('X', '.')
                    tot_val_avaliado = '{:,.2f}'.format(tot_val_avaliado).replace(',', 'X').replace('.', ',').replace('X', '.')
                    tot_itbi_apurado = '{:,.2f}'.format(tot_itbi_apurado).replace(',', 'X').replace('.', ',').replace('X', '.')
                    tot_itbi_pago = '{:,.2f}'.format(tot_itbi_pago).replace(',', 'X').replace('.', ',').replace('X', '.')
                    tot_itbi_declarado = '{:,.2f}'.format(tot_itbi_declarado).replace(',', 'X').replace('.', ',').replace('X', '.')
                    tot_incremento_itbi = '{:,.2f}'.format(tot_incremento_itbi).replace(',', 'X').replace('.', ',').replace('X', '.')

                    pdf.add_font('Calibri', fname='fonts/Calibri.ttf', uni=True)
                    pdf.set_font('Calibri', size=6)
                    pdf.cell(1, 5, txt=f'{tot_registros} Registro(s)')
                    pdf.cell(179, 5, txt=f'R$ {tot_val_declarado}', align='R')
                    pdf.cell(19, 5, txt=f'R$ {tot_itbi_declarado}', align='R')
                    pdf.cell(19, 5, txt=f'R$ {tot_val_avaliado}', align='R')
                    pdf.cell(19, 5, txt=f'R$ {tot_itbi_apurado}', align='R')
                    pdf.cell(19, 5, txt=f'R$ {tot_itbi_pago}', align='R')
                    pdf.cell(20, 5, txt=f'R$ {tot_incremento_itbi}', align='R')
                    pdf.ln(2) 

                    pdf.add_font('Calibri', fname='fonts/Calibri.ttf', uni=True)
                    pdf.set_font('Calibri', size=6)
                    pdf.set_y(-40)
                    pdf.cell(0, 10, txt='Obs: Os valores obtidos na coluna "Incremento ITBI" são resultado da subtração "ITBI Apurado" - "ITBI Declarado".', align='L')

                    temp_file = tempfile.NamedTemporaryFile(delete=False)
                    pdf.output(temp_file.name)
                    temp_file.close()

                    with open(temp_file.name, 'rb') as file:
                        pdf_content = file.read()
                    
                    os.unlink(temp_file.name)

                    response = HttpResponse(pdf_content, content_type='application/pdf')
                    response['Content-Disposition'] = 'inline; filename="avaliacoes_itbi_apurado.pdf"' 

                    return response
                
            elif filtro_modelo == '2':
                """
                    RELATÓRIO - INCREMENTO DE ITBI PAGO
                """

                pdf.set_fill_color(211,211,211) 
                pdf.cell(98 * 0.7, 4, 'Contribuinte', 1, align='C', fill=True) 
                pdf.cell(18 * 0.7, 4, 'Processo', 1, align='C', fill=True)
                pdf.cell(27 * 0.7, 4, 'Matrícula', 1, align='C', fill=True)
                pdf.cell(20 * 0.7, 4, 'Finalidade', 1, align='C', fill=True)
                pdf.cell(19 * 0.7, 4, 'Área', 1, align='C', fill=True)
                pdf.cell(48 * 0.7, 4, 'Operação', 1, align='C', fill=True)
                pdf.cell(27 * 0.7, 4, 'Val. Declarado', 1, align='C', fill=True)
                pdf.cell(27 * 0.7, 4, 'ITBI Declarado', 1, align='C', fill=True)
                pdf.cell(27 * 0.7, 4, 'Val. Avaliado', 1, align='C', fill=True)
                pdf.cell(27 * 0.7, 4, 'ITBI Apurado', 1, align='C', fill=True)
                pdf.cell(27 * 0.7, 4, 'ITBI Pago', 1, align='C', fill=True)
                pdf.cell(29 * 0.7, 4, 'Incremento ITBI', 1, align='C', fill=True)
                pdf.ln()

                if filtro_municipio:
                    processos_filtrados = Processo.objects.filter(municipio_id=filtro_municipio, ativo=True).order_by('contribuinte__nome_contribuinte')
                    
                    tot_registros = 0
                    tot_val_declarado = 0
                    tot_val_avaliado = 0
                    tot_itbi_apurado = 0
                    tot_itbi_pago = 0
                    tot_itbi_declarado = 0
                    tot_incremento_itbi = 0
                    
                    for processo in processos_filtrados:
                        if len(str(processo.numero)) > 4:
                            numero_processo = f'{str(processo.numero)[:-4]}/{str(processo.numero)[-4:]}'
                        else:
                            numero_processo = processo.numero

                        avaliacoes_filtradas = Avaliacao.objects.filter(andamento__processo=processo, ativo=True).order_by('sequencial')

                        if filtro_data_ava_ini and filtro_data_ava_fin:
                            if filtro_data_ava_ini != filtro_data_ava_fin:
                                avaliacoes_filtradas = avaliacoes_filtradas.filter(data_avaliacao__range=(filtro_data_ava_ini, filtro_data_ava_fin))
                            else:
                                avaliacoes_filtradas = avaliacoes_filtradas.filter(data_avaliacao=filtro_data_ava_ini)
                        elif filtro_data_ava_ini:
                            avaliacoes_filtradas = avaliacoes_filtradas.filter(data_avaliacao=filtro_data_ava_ini)
                        elif filtro_data_ava_fin:
                            avaliacoes_filtradas = avaliacoes_filtradas.filter(data_avaliacao=filtro_data_ava_fin)
                        
                        if filtro_andamento_avaliacao:
                            avaliacoes_filtradas = avaliacoes_filtradas.filter(tipo_andamento_avaliacao=filtro_andamento_avaliacao)

                        if avaliacoes_filtradas:
                            for avaliacao in avaliacoes_filtradas:
                                tot_registros += 1
                                
                                if avaliacao.finalidade:
                                    finalidade = avaliacao.finalidade
                                else:
                                    finalidade = '-'

                                if avaliacao.area:
                                    if str(avaliacao.finalidade) == 'Urbano':
                                        area = round(avaliacao.area, 2)
                                    else:
                                        area = avaliacao.area
                                else:
                                    area = '-'

                                if avaliacao.operacao:
                                    operacao = avaliacao.operacao
                                else:
                                    operacao = '-'

                                if avaliacao.valor_declarado and avaliacao.valor_declarado > 0:
                                    tot_val_declarado += avaliacao.valor_declarado
                                    valor_declarado = '{:,.2f}'.format(avaliacao.valor_declarado).replace(',', 'X').replace('.', ',').replace('X', '.')
                                else:
                                    valor_declarado = '-'

                                if avaliacao.valor_avaliado and avaliacao.valor_avaliado > 0:
                                    tot_val_avaliado += avaliacao.valor_avaliado
                                    valor_avaliado = '{:,.2f}'.format(avaliacao.valor_avaliado).replace(',', 'X').replace('.', ',').replace('X', '.')
                                else:
                                    valor_avaliado = '-'

                                if avaliacao.valor_itbi_diferenca and avaliacao.valor_itbi_diferenca > 0:
                                    tot_itbi_apurado += avaliacao.valor_itbi_diferenca
                                    valor_itbi_diferenca = '{:,.2f}'.format(avaliacao.valor_itbi_diferenca).replace(',', 'X').replace('.', ',').replace('X', '.')   
                                else:
                                    valor_itbi_diferenca = '-'

                                if avaliacao.valor_pago_avaliacao and avaliacao.valor_pago_avaliacao > 0:
                                    tot_itbi_pago += avaliacao.valor_pago_avaliacao
                                    valor_itbi_pago = '{:,.2f}'.format(avaliacao.valor_pago_avaliacao).replace(',', 'X').replace('.', ',').replace('X', '.')                  
                                else:
                                    valor_itbi_pago = '-'

                                if avaliacao.valor_declarado:

                                    operacao_id = avaliacao.operacao.id

                                    """
                                        IDs: 5 - INTEGRALIZAÇÃO / INCORPORAÇÃO | 6 - CISÃO | 7 - FUSÃO | 8 - EXTINÇÃO DE CONDOMÍNIO | 9 - EXTINÇÃO DE PESSOA JURÍDICA
                                    """
                                    if operacao_id == 5 or operacao_id == 6 or operacao_id == 7 or operacao_id == 8 or operacao_id == 9:
                                        itbi_declarado = '-'
                                    else:
                                        itbi_declarado = avaliacao.valor_declarado * 2/100
                                        if itbi_declarado > 0:
                                            tot_itbi_declarado += itbi_declarado
                                            itbi_declarado = '{:,.2f}'.format(itbi_declarado).replace(',', 'X').replace('.', ',').replace('X', '.') 
                                        else:
                                            itbi_declarado = '-'
                                else:
                                    itbi_declarado = '-'

                                if avaliacao.valor_pago_avaliacao and avaliacao.valor_declarado:
                                    calc_itbi_declarado = avaliacao.valor_declarado * 2/100
                                    incremento_itbi =  avaliacao.valor_pago_avaliacao - calc_itbi_declarado
                                    if incremento_itbi > 0:
                                        operacao_id = avaliacao.operacao.id
                                        if operacao_id == 5 or operacao_id == 6 or operacao_id == 7 or operacao_id == 8 or operacao_id == 9:
                                            incremento_itbi = valor_itbi_pago
                                        else:
                                            tot_incremento_itbi += incremento_itbi
                                            incremento_itbi = '{:,.2f}'.format(incremento_itbi).replace(',', 'X').replace('.', ',').replace('X', '.')
                                    else:
                                        incremento_itbi = '-'
                                else:
                                    incremento_itbi = '-'
                                

                                pdf.set_font('Calibri', 'B', size=6)
                                pdf.cell(98 * 0.7, 4, str(processo.contribuinte.nome_contribuinte[:55]), 1, align='L')
                                pdf.cell(18 * 0.7, 4, str(numero_processo), 1, align='R')
                                pdf.cell(27 * 0.7, 4, str(avaliacao.matricula), 1, align='R')
                                pdf.cell(20 * 0.7, 4, str(finalidade), 1, align='C')
                                pdf.cell(19 * 0.7, 4, str(area), 1, align='R')
                                pdf.cell(48 * 0.7, 4, str(operacao), 1, align='C')
                                pdf.cell(27 * 0.7, 4, str(valor_declarado), 1, align='R')
                                pdf.cell(27 * 0.7, 4, str(itbi_declarado), 1, align='R')
                                pdf.cell(27 * 0.7, 4, str(valor_avaliado), 1, align='R')
                                pdf.cell(27 * 0.7, 4, str(valor_itbi_diferenca), 1, align='R')
                                pdf.cell(27 * 0.7, 4, str(valor_itbi_pago), 1, align='R')
                                pdf.cell(29 * 0.7, 4, str(incremento_itbi), 1, align='R')

                                pdf.ln()

                    tot_val_declarado = '{:,.2f}'.format(tot_val_declarado).replace(',', 'X').replace('.', ',').replace('X', '.')
                    tot_val_avaliado = '{:,.2f}'.format(tot_val_avaliado).replace(',', 'X').replace('.', ',').replace('X', '.')
                    tot_itbi_apurado = '{:,.2f}'.format(tot_itbi_apurado).replace(',', 'X').replace('.', ',').replace('X', '.')
                    tot_itbi_pago = '{:,.2f}'.format(tot_itbi_pago).replace(',', 'X').replace('.', ',').replace('X', '.')
                    tot_itbi_declarado = '{:,.2f}'.format(tot_itbi_declarado).replace(',', 'X').replace('.', ',').replace('X', '.')
                    tot_incremento_itbi = '{:,.2f}'.format(tot_incremento_itbi).replace(',', 'X').replace('.', ',').replace('X', '.')

                    pdf.add_font('Calibri', fname='fonts/Calibri.ttf', uni=True)
                    pdf.set_font('Calibri', size=6)
                    pdf.cell(1, 5, txt=f'{tot_registros} Registro(s)')
                    pdf.cell(179, 5, txt=f'R$ {tot_val_declarado}', align='R')
                    pdf.cell(19, 5, txt=f'R$ {tot_itbi_declarado}', align='R')
                    pdf.cell(19, 5, txt=f'R$ {tot_val_avaliado}', align='R')
                    pdf.cell(19, 5, txt=f'R$ {tot_itbi_apurado}', align='R')
                    pdf.cell(19, 5, txt=f'R$ {tot_itbi_pago}', align='R')
                    pdf.cell(20, 5, txt=f'R$ {tot_incremento_itbi}', align='R')
                    pdf.ln(2) 

                    pdf.add_font('Calibri', fname='fonts/Calibri.ttf', uni=True)
                    pdf.set_font('Calibri', size=6)
                    pdf.set_y(-40)
                    pdf.cell(0, 10, txt='Obs: Os valores obtidos na coluna "Incremento ITBI" são resultado da subtração "ITBI Pago" - "ITBI Declarado".', align='L')

                    temp_file = tempfile.NamedTemporaryFile(delete=False)
                    pdf.output(temp_file.name)
                    temp_file.close()

                    with open(temp_file.name, 'rb') as file:
                        pdf_content = file.read()
                    
                    os.unlink(temp_file.name)

                    response = HttpResponse(pdf_content, content_type='application/pdf')
                    response['Content-Disposition'] = 'inline; filename="avaliacoes_itbi_apurado.pdf"' 

                    return response

                else:
                    temp_file = tempfile.NamedTemporaryFile(delete=False)
                    pdf.output(temp_file.name)
                    temp_file.close()

                    with open(temp_file.name, 'rb') as file:
                        pdf_content = file.read()

                    os.unlink(temp_file.name)

                    response = HttpResponse(pdf_content, content_type='application/pdf')
                    response['Content-Disposition'] = 'inline; filename="avaliacoes_itbi_apurado.pdf"'

                    return response

            else:
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                pdf.output(temp_file.name)
                temp_file.close()

                with open(temp_file.name, 'rb') as file:
                    pdf_content = file.read()
                
                os.unlink(temp_file.name)

                response = HttpResponse(pdf_content, content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="avaliacoes_itbi_apurado.pdf"' 

                return response


        except Exception as error:
            print(f'Error na funcao (get) - views: (RelatorioAvaliacoes) - error: {str(error)}')

class LancamentoUsuario(LoginRequiredMixin, ListView):
    model = Funcionario
    template_name = 'usuarios/lancamentos_usuario_list.html'

    def get_context_data(self, **kwargs):
        try:
            filtro_data_inicial = self.request.GET.get('data_inicial')
            filtro_data_final = self.request.GET.get('data_final')
            funcionarios = self.model.objects.filter(ativo=True).exclude(id=15).order_by('nome')
        
            for funcionario in funcionarios:
                total_uploads = 0
                id_usuario = funcionario.user_id

                processos_funcionario = Processo.objects.filter(usuario_criador_id=id_usuario, ativo=True)
                andamentos_funcionario = Andamento.objects.filter(usuario_criador_id=id_usuario, ativo=True)

                if filtro_data_inicial and filtro_data_final: 
                    if filtro_data_inicial != filtro_data_final:
                        processos_funcionario = processos_funcionario.filter(data_criacao__range=(filtro_data_inicial, filtro_data_final)) 
                        andamentos_funcionario = andamentos_funcionario.filter(data_criacao__range=(filtro_data_inicial, filtro_data_final))
                    else:
                        processos_funcionario = processos_funcionario.filter(data_criacao=filtro_data_inicial) 
                        andamentos_funcionario = andamentos_funcionario.filter(data_criacao=filtro_data_inicial)    
                
                elif filtro_data_inicial:    
                    processos_funcionario = processos_funcionario.filter(data_criacao=filtro_data_inicial)
                    andamentos_funcionario = andamentos_funcionario.filter(data_criacao=filtro_data_inicial)
                
                elif filtro_data_final:
                    processos_funcionario = processos_funcionario.filter(data_criacao=filtro_data_final) 
                    andamentos_funcionario = andamentos_funcionario.filter(data_criacao=filtro_data_final)

                for andamento in andamentos_funcionario:
                    if andamento.arquivo != '':
                        total_uploads += 1
                    if andamento.arquivo2 != '':
                        total_uploads += 1

                funcionario.total_processos = processos_funcionario.count()
                funcionario.total_andamentos = andamentos_funcionario.count()
                funcionario.total_uploads = total_uploads


            if filtro_data_inicial and filtro_data_final:
                if filtro_data_inicial != filtro_data_final:
                    soma_processos = Processo.objects.filter(data_criacao__range=(filtro_data_inicial, filtro_data_final), origem='usuario', ativo=True).count()
                    soma_andamentos = Andamento.objects.filter(data_criacao__range=(filtro_data_inicial, filtro_data_final), origem='usuario', ativo=True).count()
                else:
                    soma_processos = Processo.objects.filter(data_criacao=filtro_data_inicial, origem='usuario',).count() 
                    soma_andamentos = Andamento.objects.filter(data_criacao=filtro_data_inicial, origem='usuario',).count() 
            
            elif filtro_data_inicial:
                soma_processos = Processo.objects.filter(data_criacao=filtro_data_inicial, origem='usuario').count()
                soma_andamentos = Andamento.objects.filter(data_criacao=filtro_data_inicial, origem='usuario').count()
            
            elif filtro_data_final:
                soma_processos = Processo.objects.filter(data_criacao=filtro_data_final, origem='usuario').count()
                soma_andamentos = Andamento.objects.filter(data_criacao=filtro_data_final, origem='usuario').count()
            else:
                soma_processos = Processo.objects.filter(origem='usuario', ativo=True).count()
                soma_andamentos = Andamento.objects.filter(origem='usuario', ativo=True).count()
        
            context = super().get_context_data(**kwargs)
            context['funcionarios'] = funcionarios
            context['soma_processos'] = soma_processos
            context['soma_andamentos'] = soma_andamentos

            return context

        except Exception as error:
            print(f'Error na funcao (get_context_data) - views: (LancamentoUsuario) - error: {str(error)}')