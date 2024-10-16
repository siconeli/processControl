# import matplotlib.pyplot as plt
# import tempfile
# import os

# categorias = ['A', 'B', 'C', 'D', 'E']
# valores = [10, 23, 17, 12, 15]

# plt.bar(categorias, valores)
# plt.xlabel('Categorias')
# plt.ylabel('Valores')
# plt.title('Gráfico de Barras')
# # plt.show()
# plt.savefig('grafico.png')
# plt.close()

# criar o arquivo temporário, em seguida excluílo

# Pegar o layout do canva e preencher a página do pdf com o layout

# 

# from fpdf import FPDF
# import tempfile
# import os
# from django.http import HttpResponse

# def GerarPdf():
#     pdf = FPDF()

#     pdf.add_page()

#     pdf.cell("teste")

#     temp_file = tempfile.NamedTemporaryFile(delete=False)
#     pdf.output(temp_file.name)
#     temp_file.close()

#     with open(temp_file.name, 'rb') as file:
#         pdf_content = file.read()

#     os.unlink(temp_file.name)

#     response = HttpResponse(pdf_content, content_type='application/pdf')
#     response['Content-Disposition'] = 'inline; filename="teste.pdf"'

#     return response

# GerarPdf()