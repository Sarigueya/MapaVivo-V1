from django.db import migrations, models
import django.db.models.deletion
import recursos.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('recursos', '0001_initial'),
    ]

    operations = [
        # Agregar campo creado_por a Recurso
        migrations.AddField(
            model_name='recurso',
            name='creado_por',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='recursos',
                to='auth.user',
                verbose_name='Creado por'
            ),
        ),
        # Crear tabla Organizacion
        migrations.CreateModel(
            name='Organizacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('nombre_org', models.CharField(max_length=200, verbose_name='Nombre de la organización')),
                ('descripcion', models.TextField(verbose_name='Descripción del trabajo que realizan')),
                ('direccion', models.CharField(max_length=300, verbose_name='Dirección física')),
                ('telefono', models.CharField(blank=True, default='', max_length=30)),
                ('sitio_web', models.URLField(blank=True, default='', verbose_name='Sitio web o red social')),
                ('estado', models.CharField(
                    choices=[('pendiente','Pendiente de revisión'),('aprobada','Aprobada'),('rechazada','Rechazada')],
                    db_index=True, default='pendiente', max_length=20
                )),
                ('nota_admin', models.TextField(blank=True, default='', verbose_name='Nota del administrador')),
                ('creada_en', models.DateTimeField(auto_now_add=True)),
                ('actualizada_en', models.DateTimeField(auto_now=True)),
                ('usuario', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='organizacion',
                    to='auth.user'
                )),
            ],
            options={
                'verbose_name': 'Organización',
                'verbose_name_plural': 'Organizaciones',
                'ordering': ['-creada_en'],
            },
        ),
    ]