filtro_1 = 'marco'
filtro_2 = 'setembro'

palavras = {'janeiro': 1250, 'fevereiro': 500, 'marco': 375, 'abril':878, 'maio':6758, 'junho':656, 'julho':753, 'agosto':159, 'setembro':13150, 'outubro':789, 'novembro':456, 'dezembro': 78}

meses = list(palavras.keys())

indice_1, indice_2 = meses.index(filtro_1), meses.index(filtro_2)

valores_filtrados = {mes: palavras[mes] for mes in meses[indice_1:indice_2 +1]}

meses_intervalo = meses[indice_1:indice_2 +1]

valores_intervalo = list(palavras[mes] for mes in meses_intervalo)

