from decimal import Decimal
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import View, TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from matplotlib.patches import FancyBboxPatch
import numpy as np
from .models import Ficha, ValorMes
from apps.municipios.models import Municipio
from .models import Receita, Ano
from .forms import FichaForm, ValorMesForm
from django.core.cache import cache
import os

# Imports para gerar gráfico
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg') 

# Imports para gerar PDF
from fpdf import FPDF
import tempfile

class FichaCreate(LoginRequiredMixin, CreateView):
    model = Ficha
    template_name = 'grafico/ficha_create.html'
    form_class = FichaForm

    def form_valid(self, form):
        try:
            valor_mes_form = ValorMesForm(self.request.POST)
           
            municipio_input = form.cleaned_data['municipio']
            receita_input = form.cleaned_data['receita']
            ano_input = form.cleaned_data['ano']

            if self.model.objects.filter(municipio=municipio_input, receita=receita_input, ano=ano_input).exists():
                form.add_error(None, f'Já existe uma ficha cadastrada para: {municipio_input}, {receita_input}, {ano_input}')
                return self.render_to_response(self.get_context_data(form=form, valor_mes_form=valor_mes_form))

            if valor_mes_form.is_valid():
                ficha = form.save()
                valor_mes = valor_mes_form.save(commit=False)
                valor_mes.ficha = ficha
                valor_mes.save()
                return super().form_valid(form)
            else:
                form.add_error(None, 'Erro no formulário de Valor Mês')
                return self.render_to_response(self.get_context_data(form=form, valor_mes_form=valor_mes_form))
            
        except Exception as e:
            print(e)
            return self.render_to_response(self.get_context_data(form=form, valor_mes_form=valor_mes_form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if 'valor_mes_form' not in kwargs:
            context['valor_mes_form'] = ValorMesForm()
        else:
            context['valor_mes_form'] = kwargs['valor_mes_form']

        context['anos'] = Ano.objects.all().order_by('-nome')

        return context

    def get_success_url(self):
        try:
            cache.delete(f'fichas_filtradas_{self.request.user.pk}')
            return reverse('ficha-list') 
        except Exception as e:
            print(e)

class FichaList(LoginRequiredMixin, ListView):
    model = Ficha
    template_name = 'grafico/ficha_list.html'

    def get_queryset(self):
        try:
            usuario_pk = self.request.user.pk

            filtros = {
                'municipio': 'cache_key_municipio',
                'receita': 'cache_key_receita',
                'ano': 'cache_key_ano'
            }

            for filtro, cache_key in filtros.items():
                valor_filtro = self.request.GET.get(filtro)
                cache_key_usuario = f'{cache_key}_{usuario_pk}'
                
                if valor_filtro == '':
                    cache.delete(cache_key_usuario)
                elif valor_filtro:
                    cache.set(cache_key_usuario, valor_filtro)

            municipio_input = self.request.GET.get('municipio')
            receita_input = self.request.GET.get('receita')
            ano_input = self.request.GET.get('ano')

            cache_key_usuario_fichas_filtradas = f'fichas_filtradas_{usuario_pk}'
            cache_fichas_filtradas = cache.get(cache_key_usuario_fichas_filtradas)

            fichas_filtradas = self.model.objects.none()

            if municipio_input or municipio_input and receita_input or municipio_input and ano_input:
                fichas_filtradas = self.model.objects.all().order_by('-ano__nome')

                if municipio_input:
                    fichas_filtradas = fichas_filtradas.filter(municipio_id=municipio_input)
                if receita_input:
                    fichas_filtradas = fichas_filtradas.filter(receita=receita_input)
                if ano_input:
                    fichas_filtradas = fichas_filtradas.filter(ano=ano_input)
            
            elif cache_fichas_filtradas is not None:
                fichas_filtradas = cache_fichas_filtradas

            elif cache.get(f'cache_key_municipio_{usuario_pk}') or cache.get(f'cache_key_receita_{usuario_pk}') or cache.get(f'cache_key_ano_{usuario_pk}'):        
                fichas_filtradas = self.model.objects.all().order_by('-ano__nome')

                cache_municipio = cache.get(f'cache_key_municipio_{usuario_pk}')
                cache_receita = cache.get(f'cache_key_receita_{usuario_pk}')
                cache_ano = cache.get(f'cache_key_ano_{usuario_pk}')

                if cache_municipio:
                    fichas_filtradas = fichas_filtradas.filter(municipio_id=cache_municipio)

                if cache_receita:
                    fichas_filtradas = fichas_filtradas.filter(receita=cache_receita)

                if cache_ano: 
                    fichas_filtradas = fichas_filtradas.filter(ano=cache_ano)
            
            else:
                fichas_filtradas = self.model.objects.none()
            
            cache.set(cache_key_usuario_fichas_filtradas, fichas_filtradas)

            return fichas_filtradas
        except Exception as e:
            print(e)

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)

            filtros = {
                'municipio': 'cache_key_municipio',
                'receita': 'cache_key_receita',
                'ano': 'cache_key_ano'
            }

            for cache_key in filtros.values():
                cache_key_usuario = f'{cache_key}_{self.request.user.pk}'
                if cache.get(cache_key_usuario):
                    context[cache_key] = cache.get(cache_key_usuario)

            context['municipios'] = Municipio.objects.filter(tipo_contrato='Assessoria', ativo=True).order_by('nome')
            context['receitas'] = Receita.objects.all().order_by('nome')
            context['anos'] = Ano.objects.all().order_by('-nome')
            return context
        except Exception as e:
            print(e)

class LimpaCacheFichas(LoginRequiredMixin, View):
    def get(self, request):
        try:
            usuario_pk = self.request.user.pk

            filtros = {
                'municipio': 'cache_key_municipio',
                'receita': 'cache_key_receita',
                'ano': 'cache_key_ano'
            }

            for cache_key in filtros.values():
                cache.delete(f'{cache_key}_{usuario_pk}')
            
            cache.delete(f'fichas_filtradas_{usuario_pk}')

            return redirect(reverse('ficha-list'))
        except Exception as e:
            print(e)
    
class FichaUpdate(LoginRequiredMixin, UpdateView):
    model = Ficha
    template_name = 'grafico/ficha_update.html'
    form_class = FichaForm
    success_url = reverse_lazy('ficha-list')

    def form_valid(self, form):
        try:
            ficha = get_object_or_404(Ficha, id=self.kwargs.get('pk'))
            valor_mes = get_object_or_404(ValorMes, ficha_id=ficha.pk)

            municipio_input = form.cleaned_data['municipio']
            receita_input = form.cleaned_data['receita']
            ano_input = form.cleaned_data['ano']

            if self.model.objects.filter(municipio=municipio_input, receita=receita_input, ano=ano_input).exclude(id=ficha.pk).exists():
                form.add_error(None, f'Já existe uma ficha cadastrada para: {municipio_input}, {receita_input}, {ano_input}')
                return self.form_invalid(form)
            
            valor_mes_form = ValorMesForm(self.request.POST, instance=valor_mes)

            if valor_mes_form.is_valid():
                valor_mes_form.save()
                return super().form_valid(form)
            else:
                form.add_error(None, 'Erro no formulário de Valor Mês.')
                return self.form_invalid(form)

        except Exception as e:
            print(e)

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context['valor_mes'] = get_object_or_404(ValorMes, ficha_id=self.kwargs.get('pk'))                

            return context
        except Exception as e:
            print(e)

    def get_success_url(self):
        try:
            cache.delete(f'fichas_filtradas_{self.request.user.pk}')
            return reverse('ficha-list') 
        except Exception as e:
            print(e)

class FichaDelete(LoginRequiredMixin, DeleteView):
    model = Ficha

    def get_success_url(self):
        try:
            cache.delete(f'fichas_filtradas_{self.request.user.pk}')
            return reverse('ficha-list')
        except Exception as e:
            print(e)

class Relatorios(LoginRequiredMixin, TemplateView):
    template_name = 'grafico/ficha_reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['municipios'] = Municipio.objects.filter(tipo_contrato='Assessoria', ativo=True).order_by('nome')
        context['receitas'] = Receita.objects.all()
        context['anos'] = Ano.objects.all().order_by('-nome')
        return context
    
# Função para obter valores filtrados por meses
def get_valores_por_mes(ficha_id, mes_1, mes_2):
    if not ficha_id:
        return [0] * 12
    try:
        valor_mes = ValorMes.objects.get(ficha_id=ficha_id)
        valores = [
            valor_mes.janeiro, valor_mes.fevereiro, valor_mes.marco, valor_mes.abril,
            valor_mes.maio, valor_mes.junho, valor_mes.julho, valor_mes.agosto,
            valor_mes.setembro, valor_mes.outubro, valor_mes.novembro, valor_mes.dezembro
        ]
        # # Filtrar meses entre mes_1 e mes_2
        meses_lista = ['janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho',
                        'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
        indice_inicio = meses_lista.index(mes_1)
        indice_fim = meses_lista.index(mes_2) + 1
        return valores[indice_inicio:indice_fim]
    
    except ValorMes.DoesNotExist:
        return [0] * 12
    
# Função para formatar valores que vão em cima das barras
def formatar_valor(valor):
    valor = float(valor)
    valor = f'{valor:.0f}' 
    valor = int(valor)

    if valor >= 1_000_000:
        valor = f'{valor // 1_000_000},{(valor % 1_000_000) // 100_000}M'
    elif valor >= 1_000:
        valor = f'{valor // 1_000},{(valor % 1_000) // 100}K'
    else:
        valor = str(valor)
    return valor    

class GerarRelatorioGrafico(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            pdf = FPDF()
            pdf.add_page(orientation='L')

            modelo_id = request.GET.get('modelo')
            municipio_id = request.GET.get('municipio')
            receita_id = request.GET.get('receita')
            ano_1_id = request.GET.get('ano_1')
            ano_2_id = request.GET.get('ano_2')
            mes_1 = request.GET.get('mes_1')
            mes_2 = request.GET.get('mes_2')
            
            print(ano_1_id)

            try:
                receita = Receita.objects.get(id=receita_id)
                ano_1 = Ano.objects.get(id=ano_1_id)
                ano_2 = Ano.objects.get(id=ano_2_id)
                municipio = Municipio.objects.get(id=municipio_id)
            except Receita.DoesNotExist:
                receita = None
            except Ano.DoesNotExist:
                ano_1 = ano_2 = None

            if modelo_id == '1': # MODELO MENSAL
                # Gerar relatório vazio se a diferença de ano selecionado for maior que 1, o front-and já faz esse controle com Js, mas estou prevenindo erro de servidor.
                if ano_1 and ano_2 is not None:
                    ano_1_int = int(ano_1.nome)
                    ano_2_int = int(ano_2.nome)

                    if ano_2_int - ano_1_int != 1:

                        # Criar arquivo temporário para o PDF
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                        pdf.output(temp_file.name)  
                        temp_file.close()

                        # Retornar o PDF como resposta HTTP
                        with open(temp_file.name, 'rb') as file:
                            pdf_content = file.read()
                        os.unlink(temp_file.name)

                        response = HttpResponse(pdf_content, content_type='application/pdf')
                        response['Content-Disposition'] = 'inline; filename="grafico.pdf"'
                        return response

                # Obter fichas e valores para os dois anos
                ficha_ano_1 = Ficha.objects.filter(municipio_id=municipio_id, receita_id=receita_id, ano_id=ano_1_id).first()
                ficha_ano_2 = Ficha.objects.filter(municipio_id=municipio_id, receita_id=receita_id, ano_id=ano_2_id).first()
                valores_1 = get_valores_por_mes(ficha_ano_1, mes_1, mes_2)
                valores_2 = get_valores_por_mes(ficha_ano_2, mes_1, mes_2)

                valores_1_tot = sum(valores_1)
                valores_2_tot = sum(valores_2)

                # Configurações do gráfico
                plt.figure(figsize=(20, 6)) 
                x = np.arange(len(valores_1))
                largura = 0.40

                # Gráfico de barras
                bars1 = plt.bar(x - largura / 2, valores_1, width=largura, color='#3c94e5', label=str(ano_1))
                bars2 = plt.bar(x + largura / 2, valores_2, width=largura, color='#faa460', label=str(ano_2))

                # Remover valores do eixo y, lado esquerdo externo do gráfico
                plt.yticks([]) 

                # FUNÇÃO DE FORMATAR VALOR ESTAVA AQUI!

                # Colocando os valores na parte superior das barras, mas dentro
                for bar in bars1:
                    plt.text(
                        bar.get_x() + bar.get_width() / 2,  # Posição x centralizada
                        bar.get_height() - 5,                # Posição y um pouco abaixo do topo da barra
                        formatar_valor(bar.get_height()),     # Valor formatado
                        ha='center', va='bottom',              # Alinhamento central e na parte inferior do texto
                        fontsize=10, color='black', rotation=0  # Cor do texto e tamanho da fonte
                    )

                for bar in bars2:
                    plt.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() - 5,                # Posição y um pouco abaixo do topo da barra
                        formatar_valor(bar.get_height()),
                        ha='center', va='bottom',              # Alinhamento central e na parte inferior do texto
                        fontsize=10, color='black', rotation=0  # Cor do texto e tamanho da fonte
                    )

                # Rótulos e legenda
                # plt.ylabel('Valores')
                # plt.xlabel('Valor em R$', fontsize=15)

                # Rótulos de meses e conversão explícita de strings
                meses_lista = ['janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
                lista_footer_grafico = meses_lista[meses_lista.index(mes_1):meses_lista.index(mes_2) + 1]
                lista_footer_grafico = [mes[:3].title() for mes in lista_footer_grafico]

                # plt.xticks(x, [mes[:3].title() for mes in meses_lista], fontsize=10) # Configuração da legenda de meses na parte inferior do gráfico.
                plt.xticks(x, lista_footer_grafico, fontsize=10) # Configuração da legenda de meses na parte inferior do gráfico.
                plt.legend()

                # Salvar o gráfico em um arquivo temporário
                temp_image = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                plt.savefig(temp_image.name, format='png')
                plt.close()

                # Adicionar o gráfico ao PDF
                pdf.image(temp_image.name, x=-31, y=12, w=350)

                # Adicionar o brasão do município ao PDF
                try:
                    pdf.image('static/img/camapua.png', x=10, y=1, w=25, h=22)
                except:
                    pdf.image('static/img/brasao.png', x=10, y=1, w=25, h=22)
                    
                # Limpar o arquivo temporário de imagem
                temp_image.close()
                os.remove(temp_image.name)

                # RETÂNGULO PARA PREENCHIMENTO DE FUNDO HEADER
                largura = 220  
                altura = 19 
                eixo_x = 38 
                eixo_y = 3  
                pdf.set_xy(eixo_x, eixo_y) # Define a posição de acordo com eixo x e y
                pdf.set_font("Arial", style='B', size=15)
                pdf.set_fill_color(18,161,215)  # Valores de cor RGB, cor de fundo
                pdf.cell(largura, altura, ln=True, align='C', fill=True)

                # TEXTO ->  MUNICÍPIO
                eixo_x = 20  
                eixo_y = 7
                pdf.set_xy(eixo_x, eixo_y)
                pdf.set_font("Arial", style='B', size=12)
                pdf.set_fill_color(200, 200, 200)  # Valores de cor RGB, cor de fundo
                pdf.set_text_color(255,255,255)
                pdf.cell(0, 0, txt=f"MUNICÍPIO DE {municipio.nome.upper()}", ln=True, align='C')

                # TEXTO ->  FIXO
                eixo_x = 20  
                eixo_y = 13
                pdf.set_xy(eixo_x, eixo_y)
                pdf.set_font("Arial", style='B', size=12)
                pdf.set_fill_color(200, 200, 200)  # Valores de cor RGB, cor de fundo
                pdf.set_text_color(255,255,255)
                pdf.cell(0, 0, txt="ARRECADAÇÃO MENSAL DE TRIBUTOS", ln=True, align='C')

                # TEXTO -> RECEITA
                eixo_x = 20  
                eixo_y = 19
                pdf.set_xy(eixo_x, eixo_y)
                pdf.set_font("Arial", style='B', size=12)
                pdf.set_fill_color(200, 200, 200)  # Valores de cor RGB, cor de fundo
                pdf.set_text_color(255,255,255)
                pdf.cell(0, 0, txt=str(receita.nome) if receita else "N/A", ln=True, align='C')

                pdf.image('static/img/aeg5.png', x=260, y=1, w=25, h=22)

                # CABEÇALHO -> TABELA DE VALORES
                eixo_x = 13
                eixo_y = 112
                pdf.set_xy(eixo_x, eixo_y)
                pdf.set_font('Arial', 'B', size=7) 
                pdf.set_line_width(0.1) 
                pdf.set_fill_color(18,161,215)
                pdf.cell(77 * 0.7, 4, 'MÊS', 1, align='C', fill=True) 
                pdf.cell(78 * 0.7, 4, ano_1.nome, 1, align='C', fill=True) 
                pdf.cell(78 * 0.7, 4, ano_2.nome, 1, align='C', fill=True) 
                pdf.cell(78 * 0.7, 4, 'INCREMENTO R$', 1, align='C', fill=True) 
                pdf.cell(77 * 0.7, 4, 'INCREMENTO %', 1, align='C', fill=True) 
            
                incremento_real_tot = 0
                incremento_porc_tot = 0

                linha_list = []
                cont = 0
                for valor in valores_1: # Poderia ser valores_2, tanto faz, pois as duas listas possuem 12 valores, se o usuário não informar o valor, por padrão será zero.
                    incremento_real = valores_2[cont] - valores_1[cont]

                    if incremento_real >= 1: # Se o incremento for positivo, quer dizer que os dois valores são maior que zero.
                        incremento_real_tot += incremento_real
                        incremento_porc = (((incremento_real / valores_1[cont]) * 100))
                        incremento_porc_tot += incremento_porc
                        incremento_porc = f'{incremento_porc:.1f} %'.replace('.', ',')
                    else:
                        incremento_porc = '-'

                    val_ano_1 = f'R$ {valores_1[cont]:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
                    val_ano_2 = f'R$ {valores_2[cont]:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


                    incremento_real = f'R$ {incremento_real:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

                    linha = {
                        'mes': meses_lista[cont].title(),
                        'val_ano_1': val_ano_1,
                        'val_ano_2': val_ano_2, 
                        'incremento_real': incremento_real, 
                        'incremento_porc': incremento_porc
                    }

                    linha_list.append(linha)
                    cont += 1

                eixo_x = 13
                eixo_y = 116
                for linha in linha_list:
                    pdf.set_xy(eixo_x, eixo_y)
                    pdf.set_font('Arial', size=8) 
                    pdf.set_text_color(0, 0, 0)
                    pdf.cell(77 * 0.7, 4, linha['mes'], 1, align='C')
                    pdf.cell(78 * 0.7, 4,  linha['val_ano_1'], 1, align='C')
                    pdf.cell(78 * 0.7, 4, linha['val_ano_2'], 1, align='C')
                    pdf.cell(78 * 0.7, 4, linha['incremento_real'], 1, align='C')
                    pdf.cell(77 * 0.7, 4, linha['incremento_porc'], 1, align='C')
                    eixo_y += 4 # Adiciono 4 a cada linha, para que as linhas não fiquem uma em cima da outra.

                valores_1_tot = f'R$ {valores_1_tot:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
                valores_2_tot = f'R$ {valores_2_tot:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
                incremento_real_tot = f'R$ {incremento_real_tot:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
                incremento_porc_tot = f'{incremento_porc_tot:.1f} %'.replace('.', ',')

                eixo_x = 13
                eixo_y = eixo_y # Começa do eixo_y da linha de valores à cima
                pdf.set_xy(eixo_x, eixo_y)
                pdf.set_font('Arial', size=8) 
                pdf.set_text_color(0, 0, 0) 
                pdf.cell(77 * 0.7, 4, '', align='C') # Remover o ,1 para retirar as linhas da tabela e deixar somente o valor
                pdf.cell(78 * 0.7, 4,  valores_1_tot, align='C')
                pdf.cell(78 * 0.7, 4, valores_2_tot, align='C')
                pdf.cell(78 * 0.7, 4, incremento_real_tot, align='C')
                pdf.cell(77 * 0.7, 4, incremento_porc_tot, align='C')
                pdf.ln(7)

                # Definir coordenadas e dimensões da borda
                x = 122  # Posição x inicial
                y = pdf.get_y()  # Posição y atual
                width = 77 * 0.7  # Largura total das células
                height = 4 * 2  # Altura total das células (duas linhas de altura 4)
                # Desenhar borda ao redor das células
                pdf.rect(x, y, width, height)
                pdf.set_x(122)
                pdf.cell(77 * 0.7, 4, 'PERÍODO DE COMPARAÇÃO', align='C', ln=True)
                pdf.set_x(122)
                pdf.cell(77 * 0.7, 4, f'{mes_1[:3].upper()} - {mes_2[:3].upper()} DE {ano_1.nome} A {ano_2.nome}', align='C', ln=True)

                # RETÂNGULO PARA PREENCHIMENTO DE FUNDO FOOTER
                largura = 272 
                altura = 8
                eixo_x = 13 
                eixo_y = 181
                pdf.set_xy(eixo_x, eixo_y) # Define a posição de acordo com eixo x e y
                pdf.set_font("Arial", style='B', size=15)
                pdf.set_fill_color(18,161,215)  # Valores de cor RGB, cor de fundo
                pdf.cell(largura, altura, ln=True, align='C', fill=True)

                eixo_x = 121
                eixo_y = 183
                pdf.set_xy(eixo_x, eixo_y)
                pdf.set_font('Arial', style='B', size=10) 
                pdf.set_text_color(255, 255, 255) 
                pdf.cell(77 * 0.7, 4, 'AEG - ASSESSORAMENTO E CONSULTORIA TRIBUTÁRIA LTDA | RUA 14 DE JULHO, 4576 | CAMPO GRANDE - MS | AEGCONSULTORIA@ISSQN.NET', align='C')

                # Criar arquivo temporário para o PDF
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                pdf.output(temp_file.name)  
                temp_file.close()

                # Retornar o PDF como resposta HTTP
                with open(temp_file.name, 'rb') as file:
                    pdf_content = file.read()
                os.unlink(temp_file.name)

                response = HttpResponse(pdf_content, content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="grafico.pdf"'
                return response

            elif modelo_id == '2': # MODELO ANUAL
                pdf = FPDF()
                pdf.add_page(orientation='L')

                anos_filtrados = Ano.objects.filter(nome__range=(ano_1, ano_2)).order_by('nome')
                
                pdf.set_xy(13, 130)
                pdf.set_font('Arial', size=8) 
                pdf.set_text_color(0, 0, 0)
                pdf.cell(77 * 0.7, 4, 'ANO', 1, align='C')
                pdf.cell(78 * 0.7, 4,  'VALOR', 1, align='C')
                pdf.cell(78 * 0.7, 4, 'INCREMENTO R$', 1, align='C')
                pdf.cell(78 * 0.7, 4, 'INCREMENTO %', 1, align='C', ln=True)

                ano_val_list = []
                tot_ano_anterior = 0
                tot_soma_anos = 0
                incremento_real_tot = 0
                incremento_porc_tot = 0
                for ano in anos_filtrados:
                    try:
                        ficha = Ficha.objects.get(municipio_id=municipio_id, receita_id=receita_id, ano_id=ano.id)
                        valores = get_valores_por_mes(ficha.id, mes_1, mes_2)
                        tot_ano = sum(valores)
                        ano_val_list.append(tot_ano)
                        tot_soma_anos += tot_ano
                        incremento_real = tot_ano - tot_ano_anterior

                        if incremento_real != tot_ano and incremento_real > 0:
                            incremento_real_tot += incremento_real

                    except:
                        tot_ano = 0
                        incremento_real = 0

                    if tot_ano_anterior != 0 and tot_ano != 0:
                        incremento_porc = (incremento_real/tot_ano_anterior) * 100
                        if incremento_porc > 0:
                            incremento_porc_tot += incremento_porc
                        incremento_porc_str = f'{incremento_porc:.1f} %'.replace('.', ',')
                    else:
                        incremento_porc_str = ''
                    
                    tot_ano_anterior = tot_ano

                    tot_ano_str = f'R$  {tot_ano:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
                    incremento_real_str = f'R$  {incremento_real:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

                    if incremento_real == tot_ano:
                        incremento_real_str = ''

                    pdf.set_x(13)
                    pdf.cell(77 * 0.7, 4, ano.nome, 1, align='C')
                    pdf.cell(78 * 0.7, 4,  tot_ano_str, 1, align='C')
                    pdf.cell(78 * 0.7, 4, incremento_real_str, 1, align='C')
                    pdf.cell(78 * 0.7, 4, incremento_porc_str, 1, align='C', ln=True)

                tot_soma_anos_str = f'R$  {tot_soma_anos:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
                incremento_real_tot_str = f'R$  {incremento_real_tot:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
                incremento_porc_tot_str = f'{incremento_porc_tot:.1f} %'.replace('.', ',')
            
                pdf.cell(77 * 0.7, 4, '', align='C')
                pdf.cell(78 * 0.7, 4,  tot_soma_anos_str, align='C')
                pdf.cell(78 * 0.7, 4, incremento_real_tot_str, align='C')
                pdf.cell(78 * 0.7, 4, incremento_porc_tot_str, align='C', ln=True)

                plt.figure(figsize=(20, 6)) 
                x = np.arange(len(anos_filtrados))
                largura = 0.40

                nome_ano_list = [ano.nome for ano in anos_filtrados]
                val_ano_list = [val for val in ano_val_list]
                cores = ['skyblue', 'salmon', 'lightgreen', 'gold', 'red'] 

                # Remover valores do eixo y, lado esquerdo externo do gráfico
                plt.yticks([]) 

                barras = plt.bar(nome_ano_list, val_ano_list, width=largura, color=cores, label=nome_ano_list)

                # Colocando os valores na parte superior das barras
                for bar in barras:
                    plt.text(
                        bar.get_x() + bar.get_width() / 2,  # Posição x centralizada
                        bar.get_height() - 5,                # Posição y um pouco abaixo do topo da barra
                        formatar_valor(bar.get_height()),     # Valor formatado
                        ha='center', va='bottom',              # Alinhamento central e na parte inferior do texto
                        fontsize=10, color='black', rotation=0  # Cor do texto e tamanho da fonte
                    )



                # Salvar o gráfico em um arquivo temporário
                temp_image = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                plt.savefig(temp_image.name, format='png')
                plt.close()

                # Adicionar o gráfico ao PDF
                pdf.image(temp_image.name, x=-31, y=12, w=350)

                # Criar arquivo temporário para o PDF
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                pdf.output(temp_file.name)  
                temp_file.close()

                # Retornar o PDF como resposta HTTP
                with open(temp_file.name, 'rb') as file:
                    pdf_content = file.read()
                os.unlink(temp_file.name)

                response = HttpResponse(pdf_content, content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="grafico.pdf"'
                return response
        except Exception as e:
            print(f'GerarRelatorioGrafico -> {e}')
