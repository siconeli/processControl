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
                fichas_filtradas = self.model.objects.all().order_by('-ano')

                if municipio_input:
                    fichas_filtradas = fichas_filtradas.filter(municipio_id=municipio_input)
                if receita_input:
                    fichas_filtradas = fichas_filtradas.filter(receita=receita_input)
                if ano_input:
                    fichas_filtradas = fichas_filtradas.filter(ano=ano_input)
            
            elif cache_fichas_filtradas is not None:
                fichas_filtradas = cache_fichas_filtradas

            elif cache.get(f'cache_key_municipio_{usuario_pk}') or cache.get(f'cache_key_receita_{usuario_pk}') or cache.get(f'cache_key_ano_{usuario_pk}'):        
                fichas_filtradas = self.model.objects.all().order_by('-ano')

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
            context['anos'] = Ano.objects.all().order_by('nome')
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
        context['anos'] = Ano.objects.all()
        return context

def rounded_bar(ax, x, height, width=0.4, color='b'):
    """Cria uma barra com bordas arredondadas."""
    # Cria um retângulo com cantos arredondados
    bar = FancyBboxPatch((x - width / 2, 0), width, height, boxstyle="round,pad=0.05", color=color)
    ax.add_patch(bar)


class GerarRelatorioGrafico(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        pdf = FPDF()
        pdf.add_page()

        # Layout do gráfico, criado no canva
        pdf.image('static/img/layout.png', 0, 0, 210, 297)

        pdf.image('static/img/logo-empresa.png', 10, 2, 22) #x=30, y=40, tamanho imagem=230

        municipio_id= request.GET.get('municipio') # -> Retorna o ID do município
        receita_id= request.GET.get('receita')
        ano_1_id = request.GET.get('ano_1')
        ano_2_id = request.GET.get('ano_2')
        mes_1 = request.GET.get('mes_1') # -> Retorna string com o nome do mês
        mes_2 = request.GET.get('mes_2')

        try:
            receita = Receita.objects.get(id=receita_id)
        except:
            receita = ''

        try:
            ano_1 = Ano.objects.get(id=ano_1_id)
        except:
            ano_1 = ''

        try:
            ano_2 = Ano.objects.get(id=ano_2_id)
        except:
            ano_2 = ''

        valores = [0] * 12

        # Ficha 1
        if municipio_id and receita_id and ano_1_id:
            try:
                ficha = Ficha.objects.get(municipio_id=municipio_id, receita_id=receita_id, ano_id=ano_1_id)
            except:
                ficha = None

            if ficha:
                try:
                    valor_mes = ValorMes.objects.get(ficha_id=ficha.id)
                except:
                    valor_mes = None

                if valor_mes:
                    valores_1 = [valor_mes.janeiro, valor_mes.fevereiro, valor_mes.marco, valor_mes.abril, valor_mes.maio, valor_mes.junho, valor_mes.julho, valor_mes.agosto, valor_mes.setembro, valor_mes.outubro, valor_mes.novembro, valor_mes.dezembro] 

                    objeto = {'janeiro':valor_mes.janeiro, 'fevereiro':valor_mes.fevereiro, 'marco':valor_mes.marco, 'abril':valor_mes.abril, 'maio':valor_mes.maio, 'junho':valor_mes.junho, 'julho':valor_mes.julho, 'agosto':valor_mes.agosto, 'setembro':valor_mes.setembro, 'outubro':valor_mes.outubro, 'novembro':valor_mes.novembro, 'dezembro':valor_mes.dezembro}

                    meses_list = list(objeto.keys())

                    indice_filtro_1, indice_filtro_2 = meses_list.index(mes_1), meses_list.index(mes_2)

                    meses = meses_list[indice_filtro_1:indice_filtro_2 +1]

                    valores_1 = list(objeto[mes] for mes in meses )           

        else:
            valores_1 = valores

        # Ficha 2
        if municipio_id and receita_id and ano_2_id:
            try:
                ficha = Ficha.objects.get(municipio_id=municipio_id, receita_id=receita_id, ano_id=ano_2_id)
            except:
                ficha = None

            if ficha:
                try:
                    valor_mes = ValorMes.objects.get(ficha_id=ficha.id)
                except:
                    valor_mes = None

                if valor_mes:
                    valores_2 = [valor_mes.janeiro, valor_mes.fevereiro, valor_mes.marco, valor_mes.abril, valor_mes.maio, valor_mes.junho, valor_mes.julho, valor_mes.agosto, valor_mes.setembro, valor_mes.outubro, valor_mes.novembro, valor_mes.dezembro] 

                    objeto = {'janeiro':valor_mes.janeiro, 'fevereiro':valor_mes.fevereiro, 'marco':valor_mes.marco, 'abril':valor_mes.abril, 'maio':valor_mes.maio, 'junho':valor_mes.junho, 'julho':valor_mes.julho, 'agosto':valor_mes.agosto, 'setembro':valor_mes.setembro, 'outubro':valor_mes.outubro, 'novembro':valor_mes.novembro, 'dezembro':valor_mes.dezembro}

                    meses_list = list(objeto.keys())

                    indice_filtro_1, indice_filtro_2 = meses_list.index(mes_1), meses_list.index(mes_2)

                    meses = meses_list[indice_filtro_1:indice_filtro_2 +1]

                    valores_2 = list(objeto[mes] for mes in meses )  
                    print(valores_2[0])
        else:
            valores_2 = valores

        # Configurações do gráfico, largura e Altura
        plt.figure(figsize=(20,10))

        x = np.arange(len(meses))  # Posiciona os meses
        largura = 0.40  # Largura das barras(ajustável)

        # Gráfico de barras 
        bars1 = plt.bar(x - largura/2, valores_1, width=largura, color='#3c94e5', label=ano_1)   # Ajusta para a esquerda
        bars2 = plt.bar(x + largura/2, valores_2, width=largura, color='#faa460', label=ano_2)  # Ajusta para a direita

        # # Gráfico de linhas
        # plt.plot(meses_1, valores_1, marker='o', linestyle='-', color='b', label=ano_1)
        # plt.plot(meses_2, valores_2, marker='o', linestyle='--', color='r', label=ano_2)

        # Função para formatar o valor em R$
        def formatar_valor(valor):
            return f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

        # Adicionar valores em cima das barras com formatação R$
        for bar in bars1:
            yval = bar.get_height()  # Obtém a altura da barra
            plt.text(bar.get_x() + bar.get_width() / 2, yval, formatar_valor(yval), ha='center', va='bottom')  # Adiciona o texto com rotação

        for bar in bars2:
            yval = bar.get_height()  # Obtém a altura da barra
            plt.text(bar.get_x() + bar.get_width() / 2, yval, formatar_valor(yval), ha='center', va='bottom')  # Adiciona o texto com rotação

        # Alterar a cor de fundo da área do gráfico
        plt.gca().set_facecolor('#eeeeee') 

        # Título e rótulos
        # plt.title('Gráfico de Arrecadação de Tributos')
        plt.ylabel('Valores', fontsize=14)
        plt.xlabel('Meses', fontsize=14)
        plt.xticks(x, meses, fontsize=15)  # Rótulos dos meses
        plt.yticks(fontsize=14)  # Rótulos da média de valores
        plt.legend()  # Exibir legenda

        # Salvar o gráfico como imagem
        plt.savefig('static/img/grafico.png')  # Salva o gráfico
        plt.close()  # Fecha a figura para liberar memória

        # Imagem do gráfico
        pdf.image('static/img/grafico.png', -15, 25, 240) #x=-15, y=22, tamanho imagem=240

        pdf.set_font("Arial", style='B', size=15)  # Defina a fonte e o tamanho
        pdf.set_text_color(255, 255, 255)  # RGB para branco
        pdf.cell(200, 2, txt="ARRECADAÇÃO MENSAL DE TRIBUTOS", ln=True, align='C')

        # Text Receita
        pdf.set_font("Arial", style='B', size=15)  # Defina a fonte e o tamanho
        pdf.set_text_color(255, 255, 255)  # RGB para branco
        pdf.cell(200, 12, txt=receita.nome, ln=True, align='C')

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