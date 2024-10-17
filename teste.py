# import matplotlib
# import matplotlib.pyplot as plt
# matplotlib.use('Agg') 

# class RelatorioGrafico(LoginRequiredMixin, View):
#     def get(self, request):
#         pdf = FPDF()
#         pdf.add_page()

#         pdf.image('static/img/layout.png', 0, 0, 210, 297)

        
#         categorias = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
#         valores = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10 , 11, 0]
        
#         largura_colunas = 0.8

#         plt.figure(figsize=(20,10))

#         plt.bar(categorias, valores, width=largura_colunas)
        
#         plt.title('Gráfico de arrecadação de tributos')
        
#         plt.ylabel('Valores')
        
#         plt.xlabel('Meses')
        
#         # Verificar como criar o gráfico como uma imagem temporária apenas para ser incluida no relatório, depois excluir.
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






# import matplotlib
# import matplotlib.pyplot as plt
# # matplotlib.use('Agg')

# categorias = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
# valores = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10 , 11, 0]

# import matplotlib.pyplot as plt

# # Dados
# categorias = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
# valores = [100.00, 535.000, 250.000, 300.000, 150.000, 375.000, 175.000, 589.000, 456.000, 753.000, 963.000, 159.000]

# # # Configurações do gráfico
# plt.figure(figsize=(20,10))

# # Gráfico de linhas ao invés de barras
# plt.plot(categorias, valores, marker='o', linestyle='-', color='b')

# # Título e rótulos
# plt.title('Gráfico de arrecadação de tributos')
# plt.ylabel('Valores')
# plt.xlabel('Meses')

# plt.show()
