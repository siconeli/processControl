from .models import Funcionario
from apps.municipios.models import Municipio
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy

class FuncionarioCreate(LoginRequiredMixin, CreateView):
    model = Funcionario
    fields = ['user', 'foto', 'nome', 'empresa', 'departamento', 'municipio', 'documento1', 'documento2', 'documento3']
    template_name = 'funcionarios/funcionario_create.html'
    success_url = reverse_lazy('funcionario-create')

    def form_valid(self, form):
        try:
            form.instance.usuario_criador = self.request.user
            
            return super().form_valid(form)
        
        except Exception as error:
            print(f'Error na funcao (form_valid) - views: (FuncionarioCreate) - error: {str(error)}')

    def get_form(self, form_class=None):
        """
            Estou passando para o select de user(usuário) apenas usuários que não possuem vínculo com cadastro de funcionário
        """
        try:
            form = super().get_form(form_class)
            form.fields['user'].queryset = User.objects.filter(funcionario_user__isnull=True)
            form.fields['municipio'].queryset = Municipio.objects.filter(tipo_contrato='Assessoria', ativo=True).order_by('nome')
        except Exception as error:
            print(f'Error na funcao (get_form) - views: (FuncionarioCreate) - error: {str(error)}')

        return form
