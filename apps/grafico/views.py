from django.views.generic.edit import CreateView
from django.views.generic import View
from apps.municipios.models import Municipio
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ficha
from django.http import HttpResponse
import os
from django.urls import reverse

# Imports para gerar gráfico
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg') 

# Imports para gerar PDF
from fpdf import FPDF
import tempfile

class FichaCreate(LoginRequiredMixin, CreateView):
    model = Ficha
    template_name = 'fichas/ficha_create.html'

    def get_form(self, form_class=None):
        try:
            form = super().get_form(form_class)
            form.fields['municipio'].queryset = Municipio.objects.filter(tipo_contrato='Assessoria', origem='usuario', ativo=True).order_by('nome')

            return form

        except Exception as e:
            print(f'Error na função (get_form) - views: (FichaCreate) - error: {e}')

    def get_success_url(self):
        try:
            return reverse('ficha-create')
    
        except Exception as e:  
            print(f'Error na função (get_success_url) - views: (FichaCreate) - error: {e}')

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