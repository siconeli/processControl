# Generated by Django 5.1.1 on 2024-10-21 15:27

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('controle_de_processos', '0001_initial'),
        ('municipios', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StatusAtendimento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='TipoAtendimento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('atendimento', models.CharField(max_length=250)),
                ('codigo', models.CharField(blank=True, max_length=10, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TipoContato',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contato', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='ClienteAtendimento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_cliente', models.CharField(max_length=50)),
                ('usuario_criador', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Atendimento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('data_criacao', models.DateField(auto_now_add=True, verbose_name='data_criação')),
                ('data_alteracao', models.DateField(auto_now=True, verbose_name='Alterado')),
                ('origem', models.CharField(blank=True, default='usuario', max_length=20, null=True)),
                ('ticket', models.CharField(max_length=20)),
                ('atendimento_processo', models.CharField(blank=True, max_length=10, null=True)),
                ('data_atendimento', models.DateField()),
                ('descricao_atendimento', models.TextField(max_length=2000)),
                ('tempo', models.CharField(blank=True, max_length=10, null=True)),
                ('andamento_atendimento', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='controle_de_processos.andamento')),
                ('municipio_atendimento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='municipios.municipio')),
                ('processo_atendimento', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='controle_de_processos.processo')),
                ('usuario_criador', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('cliente_atendimento', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='registro.clienteatendimento')),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='registro.statusatendimento')),
                ('atendimento', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tipo_atendimento', to='registro.tipoatendimento')),
                ('contato', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='registro.tipocontato')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
