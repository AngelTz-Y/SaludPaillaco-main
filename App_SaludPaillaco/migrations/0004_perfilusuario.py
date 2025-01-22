# Generated by Django 5.0 on 2025-01-21 19:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App_SaludPaillaco', '0003_delete_perfilusuario'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PerfilUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rut', models.CharField(max_length=12)),
                ('telefono', models.CharField(max_length=15)),
                ('profesion', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='App_SaludPaillaco.profesion_oficio')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
