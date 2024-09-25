from django.views.generic import TemplateView
from apps.funcionarios.models import Funcionario
from django.contrib.auth.mixins import LoginRequiredMixin

class InicioView(LoginRequiredMixin, TemplateView):
    template_name = 'core/inicio.html'

    def get_context_data(self, **kwargs):
        if self.request.user.is_authenticated:
            usuario_logado = self.request.user
            funcionario = usuario_logado.funcionario_user
            empresa_id = funcionario.empresa_id
            
            context = super().get_context_data(**kwargs)

            if empresa_id == 1 :
                context['acesso_interno'] = "Liberado"
            return context

