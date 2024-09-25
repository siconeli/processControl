from django import forms
from .models import Contribuinte, Processo, Avaliacao

class ContribuinteForm(forms.ModelForm):
    class Meta:
        model = Contribuinte
        fields = ['nome_contribuinte', 'tipo_pessoa', 'documento', 'nome_fantasia', 'email', 'cep', 'logradouro', 'numero_casa', 'complemento', 'bairro', 'localidade', 'uf_contri', 'telefone', 'celular', ]
        
class ProcessoForm(forms.ModelForm):
    class Meta:
        model = Processo
        fields = ['numero', 'municipio', 'uf', 'data_div_ativa', 'valor_tributo', 'valor_multa', 'valor_credito', 'valor_atualizado', 'data_valor_atualizado', 'tipo', 'exercicio']

class AvaliacaoForm(forms.ModelForm):
    class Meta:
        model = Avaliacao
        fields = ['matricula', 'area', 'finalidade', 'data_pedido', 'data_avaliacao', 'operacao', 'tipo_andamento_avaliacao', 'responsavel', 'valor_declarado', 'valor_avaliado', 'valor_pago_avaliacao', 'data_valor_pago']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['finalidade'].queryset = self.fields['finalidade'].queryset.order_by('tipo_finalidade')
        self.fields['tipo_andamento_avaliacao'].queryset = self.fields['tipo_andamento_avaliacao'].queryset.order_by('tipo_and_aval')
        self.fields['responsavel'].queryset = self.fields['responsavel'].queryset.exclude(id=15).order_by('nome')
        self.fields['operacao'].queryset = self.fields['operacao'].queryset.exclude(id=15).order_by('tipo_ope_aval')