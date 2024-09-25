from django.db import models
from apps.core.models import Base

class Municipio(Base):
    tipo = (
        ('Assessoria', 'Assessoria'), 
        ('Sistema', 'Sistema'),
    )
    nome = models.CharField(max_length=50)
    tipo_contrato = models.CharField(max_length=100, choices=tipo, blank=True, null=True)
    contrato = models.CharField(max_length=50, blank=True, null=True)
    aliquota = models.DecimalField(decimal_places=1, max_digits=2, blank=True, null=True)

    def __str__(self):
        return self.nome
    