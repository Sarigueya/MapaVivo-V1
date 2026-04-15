from django.db import migrations, models
import recursos.models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Recurso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('tipo', models.CharField(
                    choices=[('comedor','Comedor'),('banco','Banco de alimentos'),
                             ('reparto','Reparto'),('canasta','Entrega de canastas')],
                    db_index=True, max_length=50)),
                ('descripcion', models.TextField(blank=True, default='')),
                ('direccion', models.CharField(blank=True, default='', max_length=300)),
                ('lat', models.FloatField()),
                ('lng', models.FloatField()),
                ('estado', models.CharField(
                    choices=[('open','Abierto'),('soon','Cierra pronto'),('closed','Sin stock')],
                    db_index=True, default='open', max_length=20)),
                ('requisitos', models.CharField(blank=True, default='', max_length=300)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateTimeField(db_index=True, default=recursos.models.expira_default)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Recurso',
                'verbose_name_plural': 'Recursos',
                'ordering': ['-updated_at'],
            },
        ),
    ]
