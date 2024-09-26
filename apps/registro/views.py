from django.db.models.base import Model as Model
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import Atendimento, ClienteAtendimento, TipoAtendimento, StatusAtendimento
from django.views.generic import View
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from apps.controle_de_processos.models import Processo
from apps.municipios.models import Municipio
from apps.funcionarios.models import Funcionario
from django.contrib import messages
from django.http import JsonResponse
import uuid
from django.contrib.auth.models import User
from django.http import HttpResponse
from datetime import datetime, timedelta
from django.db.models import Q
from django.core.cache import cache

# Relatórios
from fpdf import FPDF
import tempfile
import os

def ListaDeClientes(request):
    if request.method == 'GET':
        usuario_logado = request.user
        clientes = ClienteAtendimento.objects.filter(usuario_criador=usuario_logado).values('id', 'nome_cliente')
        clientes_list = list(clientes)
        return JsonResponse(clientes_list, safe=False)

def BuscarTipoAtendimento(request):
    try:
        if request.method == 'GET':
            cod_tip_atendimento = request.GET.get('cod_tip_atendimento', None)

            if cod_tip_atendimento is not None:
                tip_atendimento = TipoAtendimento.objects.filter(codigo=cod_tip_atendimento).last()
                tip_atendimento_id = tip_atendimento.id 

                data={
                'id': tip_atendimento_id,
                }

                return JsonResponse(data)
    except:
        return JsonResponse({'error': 'Tipo Andamento não encontrato (BuscaTipoAndamento)'}, status=400)

class AtendimentoCreate(LoginRequiredMixin, CreateView):
    model = Atendimento
    template_name = 'atendimentos/atendimento_create.html'
    fields = ['atendimento_processo', 'tempo', 'status', 'municipio_atendimento', 'data_atendimento', 'contato', 'atendimento', 'cliente_atendimento', 'descricao_atendimento']
    success_url = reverse_lazy('atendimento-list')

    def form_valid(self, form):
        try:
            form.instance.usuario_criador = self.request.user

            if self.model.objects.filter(ativo=True).exists():
                ultimo_id_db = self.model.objects.filter(ativo=True).latest('id').id
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

            form.instance.ticket = numero_ticket

            atendimento_processo = form.cleaned_data.get('atendimento_processo')
            if atendimento_processo:
                atendimento_processo_limpo = atendimento_processo.replace('/', '')
                form.instance.atendimento_processo = atendimento_processo_limpo
                processo = Processo.objects.get(municipio=form.instance.municipio_atendimento, numero=atendimento_processo_limpo)
                if processo:
                    form.instance.processo_atendimento = processo
            
            cache.delete('atendimentos_filtrados') 

            id_usuario = self.request.user.id
            cache.delete(f'atendimentos_filtrados_{id_usuario}') 
            
            messages.success(self.request, 'Atendimento cadastrado com sucesso.')
            return super().form_valid(form)

        except Exception as error:
            print(f'Error na funcao (form_valid) - views: (AtendimentoCreate) - error: {str(error)}')
    
    def get_form(self, form_class=None):
        try:
            form = super().get_form(form_class)
            
            form.fields['municipio_atendimento'].queryset = Municipio.objects.filter(origem='usuario', ativo=True).order_by('nome')
            
            form.fields['status'].queryset = StatusAtendimento.objects.filter().exclude(id=3)

            return form
        except Exception as error:
            print(f'Error na funcao (get_form) - views: (AtendimentoCreate) - error: {str(error)}')

class AtendimentoList(LoginRequiredMixin, ListView):
    model = Atendimento
    template_name = 'atendimentos/atendimento_list.html'

    def get_queryset(self):    
        id_usuario = self.request.user.id

        filtro_municipio_atendimento = self.request.GET.get("municipio_atendimento")
        if filtro_municipio_atendimento == '':
            cache.delete(f'filtro_municipio_atendimento_{id_usuario}')
        elif filtro_municipio_atendimento:
            cache.set(f'filtro_municipio_atendimento_{id_usuario}', filtro_municipio_atendimento)

        filtro_data_inicial = self.request.GET.get("data_inicial")
        if filtro_data_inicial == '':
            cache.delete(f'filtro_data_inicial_{id_usuario}')
        elif filtro_data_inicial:
            cache.set(f'filtro_data_inicial_{id_usuario}', filtro_data_inicial)

        filtro_data_final = self.request.GET.get("data_final")
        if filtro_data_final == '':
            cache.delete(f'filtro_data_final_{id_usuario}')
        elif filtro_data_final:
            cache.set(f'filtro_data_final_{id_usuario}', filtro_data_final)

        filtro_status = self.request.GET.get("status")
        if filtro_status == '':
            cache.delete(f'filtro_status_{id_usuario}')
        elif filtro_status:
            cache.set(f'filtro_status_{id_usuario}', filtro_status)

        filtro_funcionario = self.request.GET.get("criador")
        if filtro_funcionario == '':
            cache.delete(f'filtro_funcionario_{id_usuario}')
        elif filtro_funcionario:
            cache.set(f'filtro_funcionario_{id_usuario}', filtro_funcionario)

        filtro_ticket = self.request.GET.get("ticket")
        if filtro_ticket == '':
            cache.delete(f'filtro_ticket_{id_usuario}')
        elif filtro_ticket:
            cache.set(f'filtro_ticket_{id_usuario}', filtro_ticket)
        
        filtro_processo = self.request.GET.get("processo_atendimento")
        if filtro_processo == '':
            cache.delete(f'filtro_processo_{id_usuario}')
        elif filtro_processo:
            cache.set(f'filtro_processo_{id_usuario}', filtro_processo)

        filtro_descricao = self.request.GET.get("descricao_atendimento")
        if filtro_descricao == '':
            cache.delete(f'filtro_descricao_{id_usuario}')
        elif filtro_descricao:
            cache.set(f'filtro_descricao_{id_usuario}', filtro_descricao)

        atendimentos_filtrados_cache = cache.get(f'atendimentos_filtrados_{id_usuario}')

        if filtro_municipio_atendimento and filtro_data_inicial or filtro_data_inicial and filtro_funcionario or filtro_ticket or filtro_processo:
            atendimentos_filtrados = Atendimento.objects.filter(ativo=True).order_by("data_atendimento")

            if filtro_municipio_atendimento :
                atendimentos_filtrados = atendimentos_filtrados.filter(municipio_atendimento=filtro_municipio_atendimento)
            
            if filtro_data_inicial and filtro_data_final:
                atendimentos_filtrados = atendimentos_filtrados.filter(data_atendimento__range=(filtro_data_inicial, filtro_data_final))
            elif filtro_data_inicial:
                atendimentos_filtrados = atendimentos_filtrados.filter(data_atendimento=filtro_data_inicial)
            elif filtro_data_final:
                atendimentos_filtrados = atendimentos_filtrados.filter(data_atendimento=filtro_data_final)

            if filtro_funcionario:
                atendimentos_filtrados = atendimentos_filtrados.filter(usuario_criador_id=filtro_funcionario)

            if filtro_status:
                atendimentos_filtrados = atendimentos_filtrados.filter(status=filtro_status)  

            if filtro_ticket:
                atendimentos_filtrados = atendimentos_filtrados.filter(ticket=filtro_ticket)
            
            if filtro_processo:
                atendimentos_filtrados = atendimentos_filtrados.filter(atendimento_processo__icontains=filtro_processo) 
            if filtro_descricao:
                atendimentos_filtrados = atendimentos_filtrados.filter(descricao_atendimento__icontains=filtro_descricao) 
        
        elif atendimentos_filtrados_cache is not None:
            atendimentos_filtrados = atendimentos_filtrados_cache

        elif cache.get(f'filtro_municipio_atendimento_{id_usuario}') and cache.get(f'filtro_data_inicial_{id_usuario}') or cache.get(f'filtro_data_inicial_{id_usuario}') and cache.get(f'filtro_funcionario_{id_usuario}') or cache.get(f'filtro_ticket_{id_usuario}') or cache.get(f'filtro_processo_{id_usuario}'):
            atendimentos_filtrados = Atendimento.objects.filter(ativo=True).order_by("data_atendimento")
            
            if cache.get(f'filtro_municipio_atendimento_{id_usuario}') :
                atendimentos_filtrados = atendimentos_filtrados.filter(municipio_atendimento=cache.get(f'filtro_municipio_atendimento_{id_usuario}'))
            
            if cache.get(f'filtro_data_inicial_{id_usuario}') and cache.get(f'filtro_data_final_{id_usuario}'):
                atendimentos_filtrados = atendimentos_filtrados.filter(data_atendimento__range=(cache.get(f'filtro_data_inicial_{id_usuario}'), cache.get(f'filtro_data_final_{id_usuario}')))
            elif cache.get(f'filtro_data_inicial_{id_usuario}'):
                atendimentos_filtrados = atendimentos_filtrados.filter(data_atendimento=cache.get(f'filtro_data_inicial_{id_usuario}'))
            elif cache.get(f'filtro_data_final_{id_usuario}'):
                atendimentos_filtrados = atendimentos_filtrados.filter(data_atendimento=cache.get(f'filtro_data_final_{id_usuario}'))
            
            if cache.get(f'filtro_funcionario_{id_usuario}'):
                atendimentos_filtrados = atendimentos_filtrados.filter(usuario_criador_id=cache.get(f'filtro_funcionario_{id_usuario}'))
           
            if cache.get(f'filtro_status_{id_usuario}'):
                atendimentos_filtrados = atendimentos_filtrados.filter(status=cache.get(f'filtro_status_{id_usuario}'))

            if cache.get(f'filtro_ticket_{id_usuario}'):
                atendimentos_filtrados = atendimentos_filtrados.filter(ticket=cache.get(f'filtro_ticket_{id_usuario}')) 
            
            if cache.get(f'filtro_processo_{id_usuario}'):
                atendimentos_filtrados = atendimentos_filtrados.filter(atendimento_processo__icontains=cache.get(f'filtro_processo_{id_usuario}')) 

            if cache.get(f'filtro_descricao_{id_usuario}'):
                atendimentos_filtrados = atendimentos_filtrados.filter(descricao_atendimento__icontains=cache.get(f'filtro_descricao_{id_usuario}'))

        else:
            atendimentos_filtrados = self.model.objects.none()

        cache.set(f'atendimentos_filtrados_{id_usuario}', atendimentos_filtrados)

        return atendimentos_filtrados
    
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        usuarios = User.objects.filter(is_superuser=False).exclude(username='migracao').order_by('username')
        for usuario in usuarios:
            usuario.username = usuario.username.upper()

        filters = ['filtro_municipio_atendimento', 'filtro_data_inicial', 'filtro_data_final', 'filtro_funcionario', 'filtro_ticket', 'filtro_processo', 'filtro_descricao', 'filtro_status']
        id_usuario = self.request.user.id
        for filter in filters:
            if cache.get(f'{filter}_{id_usuario}'):
                context[filter] = cache.get(f'{filter}_{id_usuario}')

        context['usuarios'] = usuarios
        context['municipios'] = Municipio.objects.filter(ativo=True).order_by('nome')
        context['status'] = StatusAtendimento.objects.filter().order_by('id')

        return context

class AtendimentoDelete(LoginRequiredMixin, DeleteView):
    model = Atendimento
    success_url = reverse_lazy('atendimento-list')

    def get_object(self, queryset=None):
        atendimento_id = self.kwargs.get('id')
        return self.model.objects.get(id=atendimento_id)  
    
    def get_success_url(self) -> str:
        id_usuario = self.request.user.id
        cache.delete(f'atendimentos_filtrados_{id_usuario}') 
        return super().get_success_url()

class AtendimentoUpdate(LoginRequiredMixin, UpdateView):
    model = Atendimento
    template_name = 'atendimentos/atendimento_update.html'
    fields = ['atendimento_processo', 'municipio_atendimento', 'status', 'data_atendimento', 'contato', 'atendimento', 'cliente_atendimento', 'descricao_atendimento']
    success_url = reverse_lazy('atendimento-list')

    def form_valid(self, form):
        id_usuario = self.request.user.id
        cache.delete(f'atendimentos_filtrados_{id_usuario}')
        return super().form_valid(form)

    def get_object(self, queryset=None):
        try:
            atendimento_id = self.kwargs.get('id')
            return self.model.objects.get(id=atendimento_id)
        
        except Exception as error:
            print(f'Error na funcao (get_object) - views: (AtendimentoUpdate) - error: {str(error)}')

    def get_form(self, form_class=None):
        try:
            form = super().get_form(form_class)
            request_user = self.request.user

            form.fields['municipio_atendimento'].queryset = Municipio.objects.filter(origem='usuario', ativo=True).order_by('nome')

            form.fields['cliente_atendimento'].queryset = ClienteAtendimento.objects.filter(Q(usuario_criador=request_user) | Q(id=11))

            return form
        
        except Exception as error:
            print(f'Error na funcao (get_form) - views: (AtendimentoUpdate) - error: {str(error)}')

def ClienteAtendimentoCreate(request):
    if request.method == 'POST':
        nome_cliente = request.POST.get('nome_cliente')
        if nome_cliente != '':
            cliente = ClienteAtendimento(nome_cliente=nome_cliente, usuario_criador=request.user)
            cliente.save()
            return JsonResponse({'message': 'Cliente cadastrado com sucesso!'})
        else:
            return JsonResponse({'message': 'O nome não pode ser vazio!'})
    return render(request, 'atendimentos/atendimento_create.html')

class LimparCacheView(View):
    def get(self, request):
        id_usuario = self.request.user.id
        cache.delete(f'filtro_municipio_atendimento_{id_usuario}')
        cache.delete(f'filtro_data_inicial_{id_usuario}')
        cache.delete(f'filtro_data_final_{id_usuario}')
        cache.delete(f'filtro_funcionario_{id_usuario}')
        cache.delete(f'filtro_status_{id_usuario}')
        cache.delete(f'filtro_ticket_{id_usuario}')
        cache.delete(f'filtro_processo_{id_usuario}')
        cache.delete(f'filtro_descricao_{id_usuario}')
        cache.delete(f'atendimentos_filtrados_{id_usuario}')
        
        return redirect(reverse('atendimento-list'))
    
def filtrarProcessos(request):
    try:
        if request.method == 'GET':
            municipio_filter = request.GET.get('municipio_filter')
            num_processo = request.GET.get('processo')
            num_processo_limpo = num_processo.replace('/','')

            nome_contribuinte = request.GET.get('contribuinte')

            if municipio_filter:
                processos = Processo.objects.filter(municipio_id=municipio_filter, ativo=True)
                if num_processo_limpo:
                    processos = processos.filter(numero__icontains=num_processo_limpo) 

                if nome_contribuinte:
                    processos = processos.filter(contribuinte__nome_contribuinte__icontains=nome_contribuinte)    

                if not num_processo_limpo and not nome_contribuinte:
                    processos = Processo.objects.none()        

                if processos.exists():
                    dados = [
                        {   
                            'numero': f'{str(processo.numero)[:-4]}/{str(processo.numero)[-4:]}',
                            'contribuinte': processo.contribuinte.nome_contribuinte
                        }
                        for processo in processos 
                    ]
                else:
                    return JsonResponse({}, safe=False)
                    
                return JsonResponse(dados, safe=False)

            else:
                return JsonResponse({'error': 'Para o processo ser encontrado, é necessário selecionar o município!'}, status=400)
    except:
        return JsonResponse({'error': 'A busca de processos falhou!'}, status=400)

class Estrutura_Pdf(FPDF): 
    """
        Configurar o cabeçalho e o rodapé para todos os PDF gerados
    """
    def __init__(self, titulo_relatorio, x_nome_empresa, y_nome_empresa, x_titulo_rel, y_titulo_rel, usuario_gerou, data_gerou, nome_municipio, contrato_municipio, periodo, x_municipio, y_municipio, x_periodo, y_periodo, x_contrato, y_contrato):
        super().__init__() 
        self.titulo_relatorio = titulo_relatorio
        self.x_nome_empresa = x_nome_empresa
        self.y_nome_empresa = y_nome_empresa
        self.x_titulo_rel = x_titulo_rel
        self.y_titulo_rel = y_titulo_rel
        self.usuario_gerou = usuario_gerou
        self.data_gerou = data_gerou
        self.nome_municipio = nome_municipio
        self.contrato_municipio = contrato_municipio
        self.periodo = periodo
        self.x_municipio = x_municipio
        self.y_municipio = y_municipio 
        self.x_periodo = x_periodo
        self.y_periodo = y_periodo
        self.x_contrato = x_contrato
        self.y_contrato = y_contrato

    def header(self):
        self.image("static/img/empresa.png", 10, 4, 20)

        self.add_font('Calibri', 'B', fname='fonts/Calibri.ttf', uni=True)
        self.set_font('Calibri', 'B', size=12)
        self.cell(self.x_nome_empresa, self.y_nome_empresa, txt='Empresa Teste - Assessoria e Consultoria', ln=True, align='C')

        self.add_font('Calibri', 'B', fname='fonts/Calibri.ttf', uni=True)
        self.set_font('Calibri', 'B', size=12)
        self.cell(self.x_titulo_rel, self.y_titulo_rel, txt=f'{self.titulo_relatorio}', ln=True, align='C')
        
        if self.periodo:
            self.add_font('Calibri', 'B', fname='fonts/Calibri.ttf', uni=True)
            self.set_font('Calibri', 'B', size=12)
            self.cell(self.x_periodo, self.y_periodo, txt=self.periodo, ln=True, align='C')
        
        self.ln(12)

        if self.nome_municipio and self.contrato_municipio:
            self.add_font('Calibri', fname='fonts/Calibri.ttf', uni=True)
            self.set_font('Calibri', size=9)
            self.cell(self.x_municipio, self.y_municipio, txt=f'Município: {self.nome_municipio}', ln=True, align='L') 
            self.cell(self.x_contrato, self.y_contrato, txt=f'Contrato N°: {self.contrato_municipio}', ln=True, align='C') 
            self.ln(5)


    def footer(self):
        self.set_y(-15)
        self.add_font('Calibri', fname='fonts/Calibri.ttf', uni=True)
        self.set_font('Calibri', size=8)
        self.cell(0, 10, f'Página {self.page_no()}', align="C")
        self.cell(0, 10, f'Usuário: {self.usuario_gerou}  {self.data_gerou}  -  Empresa Teste ', 0, 0, 'R')

# def download_image(url):
#     try:
#         response = requests.get(url)
#         response.raise_for_status()
#         return response
#     except requests.RequestException as e:
#         print(f"Erro ao baixar a imagem: {e}")
#         return None
    
# def save_image_to_temp_file(image_response):
#     content_type = image_response.headers.get('Content-Type')
    
#     if 'image/jpeg' in content_type:
#         suffix = '.jpg'
#     elif 'image/png' in content_type:
#         suffix = '.png'
#     else:
#         print("Formato de imagem não suportado.")
#         return None

    # Cria um arquivo temporário
    # temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    # try:
    #     with open(temp_file.name, 'wb') as f:
    #         f.write(image_response.content)
    #     return temp_file.name
    # except IOError as e:
    #     print(f"Erro ao salvar a imagem temporária: {e}")
    #     return None
    # finally:
    #     temp_file.close()
    
def relatorioAtendimentos(request):
    """
        Na class AtendimentoList eu salvei a Queryset 'atendimentos_filtrados' no Cache de memória, para poder fazer um get no cache e ter acesso aqui na função de gerar o relatório.
    """
    try:
        id_usuario = request.user.id
        cached_atendimentos = cache.get(f'atendimentos_filtrados_{id_usuario}')
        if cached_atendimentos is not None:
            usuario_gerou = request.user
                        
            data_atual = datetime.now()
            data_gerou = data_atual - timedelta(hours=1) 
            data_gerou = data_gerou.strftime("%d/%m/%Y %H:%M:%S")

            filtro_data_inicial = cache.get(f'filtro_data_inicial_{id_usuario}')
            filtro_data_final = cache.get(f'filtro_data_final_{id_usuario}')
            filtro_municipio_atendimento = cache.get(f'filtro_municipio_atendimento_{id_usuario}')
            filtro_funcionario = cache.get(f'filtro_funcionario_{id_usuario}')

            if filtro_data_inicial:
                header_data_ini = str(filtro_data_inicial).split('-')
                ano, mes, dia = header_data_ini 
                header_data_ini = f'{dia}/{mes}/{ano}'
            if filtro_data_final:
                header_data_fin = str(filtro_data_final).split('-')
                ano, mes, dia = header_data_fin 
                header_data_fin = f'{dia}/{mes}/{ano}'

            if filtro_data_inicial and filtro_data_final:
                periodo = f'Relatório de Atendimento: {header_data_ini} até {header_data_fin}'
            elif filtro_data_inicial:
                periodo = f'Relatório de Atendimento: {header_data_ini} até {header_data_ini}'
            elif filtro_data_final:
                periodo = f'Relatório de Atendimento: {header_data_ini} até {header_data_ini}'
            else:
                periodo = ''

            x_municipio = 28
            y_municipio = 0

            x_periodo = 270
            y_periodo = 0

            x_contrato = 180
            y_contrato = 0

            if filtro_municipio_atendimento:
                get_municipio = Municipio.objects.get(id=filtro_municipio_atendimento)
                nome_municipio = get_municipio.nome
                contrato_municipio = get_municipio.contrato
            else:
                nome_municipio = ''
                contrato_municipio = ''

            x_nome_empresa = 270
            y_nome_empresa = -5
            x_titulo_rel = 270
            y_titulo_rel = 15
            titulo_relatorio = 'Gestão Tributária'

            pdf = Estrutura_Pdf(titulo_relatorio, x_nome_empresa, y_nome_empresa, x_titulo_rel, y_titulo_rel, usuario_gerou, data_gerou, nome_municipio, contrato_municipio, periodo, x_municipio, y_municipio, x_periodo, y_periodo, x_contrato, y_contrato)
            pdf.add_page(orientation='L')

            pdf.add_font('Calibri', 'B', fname='fonts/Calibri.ttf', uni=True)
            pdf.set_font('Calibri', 'B', size=12)

            pdf.set_fill_color(211,211,211)
            
            if filtro_municipio_atendimento:
                pdf.cell(35 * 0.7, 4, 'Ticket', align='L', fill=True) 
                pdf.cell(25 * 0.7, 4, 'Data', align='C', fill=True)
                pdf.cell(48 * 0.7, 4, 'Cliente', align='L', fill=True)
                pdf.cell(28 * 0.7, 4, 'Resp.', align='L', fill=True)
                pdf.cell(260 * 0.7, 4, 'Descrição', align='C', fill=True)
                pdf.ln()
            else:
                pdf.cell(75 * 0.7, 4, 'Município', align='L', fill=True) 
                pdf.cell(35 * 0.7, 4, 'Ticket', align='L', fill=True)
                pdf.cell(25 * 0.7, 4, 'Data', align='C', fill=True)
                pdf.cell(48 * 0.7, 4, 'Cliente', align='L', fill=True)
                pdf.cell(28 * 0.7, 4, 'Resp.', align='L', fill=True)
                pdf.cell(185 * 0.7, 4, 'Descrição', align='C', fill=True)
                pdf.ln()

            x_start = pdf.get_x()
            y_start = pdf.get_y()
            pdf.set_line_width(0.1)

            for atendimento in cached_atendimentos:
                if atendimento.data_atendimento:
                    data_atendimento = str(atendimento.data_atendimento).split('-')
                    ano, mes, dia = data_atendimento 
                    data_atendimento = f'{dia}/{mes}/{ano}'

                if atendimento.cliente_atendimento:
                    cliente = str(atendimento.cliente_atendimento)

                if filtro_municipio_atendimento:
                    pdf.add_font('Calibri', fname='fonts/Calibri.ttf', uni=True)
                    pdf.set_font('Calibri', size=8)
                    pdf.ln()
                    pdf.cell(35 * 0.7, 4, str(atendimento.ticket), align='L')
                    pdf.cell(25 * 0.7, 4, str(data_atendimento), align='C')
                    pdf.cell(48  * 0.7, 4, str(cliente[:15]), align='L')
                    pdf.cell(28 * 0.7, 4, str(atendimento.usuario_criador).upper(), align='L')
                    atendimento_str = str(atendimento.atendimento)
                    pdf.multi_cell(260 * 0.7, 4, str(f'{atendimento_str[:-4]}.\n{atendimento.descricao_atendimento}'), align='L')
                    pdf.ln() 
                    pdf.line(x_start, pdf.get_y(), x_start + 35 * 0.7 + 18 * 0.7 + 35 * 0.7 + 17 * 0.7 + 14 * 0.7 + 275 * 0.7, pdf.get_y())     
                
                else:
                    pdf.add_font('Calibri', fname='fonts/Calibri.ttf', uni=True)
                    pdf.set_font('Calibri', size=8)
                    pdf.ln()
                    pdf.cell(75 * 0.7, 4, str(atendimento.municipio_atendimento), align='L')
                    pdf.cell(35 * 0.7, 4, str(atendimento.ticket), align='L')
                    pdf.cell(25 * 0.7, 4, str(data_atendimento), align='C')
                    pdf.cell(48  * 0.7, 4, str(cliente[:15]), align='L')
                    pdf.cell(28 * 0.7, 4, str(atendimento.usuario_criador).upper(), align='L')
                    atendimento_str = str(atendimento.atendimento)
                    pdf.multi_cell(185 * 0.7, 4, str(f'{atendimento_str[:-4]}.\n{atendimento.descricao_atendimento}'), align='L')
                    pdf.ln() 
                    pdf.line(x_start, pdf.get_y(), x_start + 35 * 0.7 + 18 * 0.7 + 35 * 0.7 + 17 * 0.7 + 14 * 0.7 + 275 * 0.7, pdf.get_y())       

            pdf.add_font('Calibri', fname='fonts/Calibri.ttf', uni=True)
            pdf.set_font('Calibri', size=9)
            pdf.cell(35 * 0.7, 4, f'Total Atendimentos: {len(cached_atendimentos)}', align='L')
  
            current_y = pdf.get_y()
            pdf.set_y(-60)  
            remaining_height = pdf.page_break_trigger - current_y

            if remaining_height < 55: 
                pdf.add_page(orientation='L')  
                pdf.set_y(-60) 

            pdf.image("static/img/cartaocnpj.png", 10, pdf.get_y(), 55)
            
            if filtro_funcionario:
                funcionario = Funcionario.objects.get(user_id=filtro_funcionario)
                if funcionario.assinatura:
                    assinatura_path = funcionario.assinatura.url

                    image_response = download_image(assinatura_path)
        
                    if image_response:
                        temp_image_path = save_image_to_temp_file(image_response)

                        if temp_image_path:
                            try:
                                pdf.image(temp_image_path, x=215, y=155, w=60, h=20)
                            except Exception as e:
                                print(f"Erro ao adicionar a imagem ao PDF: {e}")

                            os.remove(temp_image_path)
                        else:
                            print("Não foi possível salvar a imagem temporária.")
                    else:
                        print("Não foi possível adicionar a imagem ao PDF.")
                else:
                    pdf.image("static/img/assinatura.png", x=215, y=155, w=60, h=20)

                x_position_linha = 200
                y_position_linha = -40 

                pdf.set_xy(x_position_linha, y_position_linha)
                pdf.cell(0, 10, str("_____________________________"), align='C')

                x_position_nome = 200
                y_position_nome = -37
                pdf.set_xy(x_position_nome, y_position_nome)
                pdf.cell(0, 10, str(funcionario.nome), align='C')

            temp_file = tempfile.NamedTemporaryFile(delete=False)
            pdf.output(temp_file.name)
            temp_file.close()

            with open(temp_file.name, 'rb') as file:
                pdf_content = file.read()
            
            os.unlink(temp_file.name)

            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="Atendimentos - {data_gerou[:10]}.pdf"'
            return response
        
        else:
            return HttpResponse('A Queryset não foi encontrada no Cache.')

    except Exception as error:
        print(f'Error na funcao (get) - views: (relatorioAtendimentos) - error: {str(error)}')
