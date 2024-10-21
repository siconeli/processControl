from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ficha
from apps.municipios.models import Municipio
from django.urls import reverse
from .forms import FichaForm, ValorMesForm

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
            municipio_input = form.cleaned_data['municipio']
            receita_input = form.cleaned_data['receita']
            ano_input = form.cleaned_data['ano']

            valor_mes_form = ValorMesForm(self.request.POST)

            if self.model.objects.filter(municipio=municipio_input, receita=receita_input, ano=ano_input).exists():
                form.add_error(None, f'Já existe uma ficha cadastrada para: {municipio_input}, {receita_input}, {ano_input}')
                return self.form_invalid(form, valor_mes_form=valor_mes_form)

            if valor_mes_form.is_valid():
                ficha = form.save()
                valor_mes = valor_mes_form.save(commit=False)
                valor_mes.ficha = ficha
                valor_mes.save()
                return super().form_valid(form)
            
            else:
                valor_mes_form.add_error(None, 'Erro no formulário de valor mês')
                return self.form_invalid(form, valor_mes_form=valor_mes_form)
            
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
            return reverse('ficha-list') 
        except Exception as e:
            print(e)

class FichaList(LoginRequiredMixin, ListView):
    model = Ficha
    template_name = 'grafico/ficha_list.html'

    def get_queryset(self):
        municipio_input = self.request.GET.get('municipio')
        receita_input = self.request.GET.get('receita')
        ano_input = self.request.GET.get('ano')

        fichas_filtradas = self.model.objects.none()

        if municipio_input:
            fichas_filtradas = self.model.objects.filter(municipio_id=municipio_input).order_by('-ano')

        return fichas_filtradas

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['municipios'] = Municipio.objects.filter(tipo_contrato='Assessoria', ativo=True).order_by('nome')
        return context


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