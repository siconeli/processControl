from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ficha, ValorMes
from apps.municipios.models import Municipio
from .models import Receita, Ano
from django.urls import reverse, reverse_lazy
from .forms import FichaForm, ValorMesForm
from django.core.cache import cache

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

# class Grafico(LoginRequiredMixin, View):
#     def get(self, request):
#         pdf = FPDF()
#         pdf.add_page()

#         pdf.image('static/img/layout.png', 0, 0, 210, 297)

#         # Criar uma condição de acordo com o tipo de relatório selecionado, "mensal ou anual"

#         # Dados
#         categorias = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
#         valores = [100.00, 535.000, 250.000, 300.000, 150.000, 375.000, 175.000, 589.000, 456.000, 753.000, 963.000, 159.000]

#         # # Configurações do gráfico
#         plt.figure(figsize=(20,10))

#         # Gráfico de linhas ao invés de barras
#         plt.plot(categorias, valores, marker='o', linestyle='-', color='b')

#         # Título e rótulos
#         plt.title('Gráfico de arrecadação de tributos')
#         plt.ylabel('Valores')
#         plt.xlabel('Meses')

#        # Verificar como criar o gráfico como uma imagem temporária apenas para ser incluida no relatório, depois excluir.
#         plt.savefig('static/img/grafico.png')
        
#         plt.close()

#         pdf.image('static/img/grafico.png', -10, 40, 230) #x=30, y=40, tamanho imagem=200

#         pdf.set_font("Arial", size=12)  # Defina a fonte e o tamanho

#         # Adicione uma célula com o texto
#         pdf.cell(200, 10, txt="Relatório de arrecadação de tributos", ln=True, align='C')

#         # Crie um arquivo temporário
#         temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
#         pdf.output(temp_file.name)

#         temp_file.close()
        
#         with open(temp_file.name, 'rb') as file:
#             pdf_content = file.read()
        
#         os.unlink(temp_file.name)  # Exclua o arquivo temporário

#         response = HttpResponse(pdf_content, content_type='application/pdf')
#         response['Content-Disposition'] = 'inline; filename="grafico.pdf"'

#         return response