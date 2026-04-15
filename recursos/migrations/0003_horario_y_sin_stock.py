from django.db import migrations, models
import recursos.models


class Migration(migrations.Migration):

    dependencies = [
        ('recursos', '0002_organizacion_y_creado_por'),
    ]

    operations = [
        # Eliminar campo estado (ahora es una propiedad calculada)
        migrations.RemoveField(model_name='recurso', name='estado'),

        # Agregar campos de horario
        migrations.AddField(
            model_name='recurso',
            name='dias_atencion',
            field=models.CharField(
                blank=True, default='lun,mar,mie,jue,vie',
                help_text='Días separados por coma: lun,mar,mie,jue,vie,sab,dom',
                max_length=50
            ),
        ),
        migrations.AddField(
            model_name='recurso',
            name='hora_apertura',
            field=models.TimeField(blank=True, null=True, help_text='Ej: 11:00'),
        ),
        migrations.AddField(
            model_name='recurso',
            name='hora_cierre',
            field=models.TimeField(blank=True, null=True, help_text='Ej: 14:00'),
        ),
        migrations.AddField(
            model_name='recurso',
            name='sin_horario',
            field=models.BooleanField(
                default=False,
                help_text='Marcar si el recurso no tiene horario fijo'
            ),
        ),
        migrations.AddField(
            model_name='recurso',
            name='sin_stock_hoy',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='recurso',
            name='sin_stock_fecha',
            field=models.DateField(blank=True, null=True),
        ),
        # Actualizar expires_at default (ya no expira en 8h)
        migrations.AlterField(
            model_name='recurso',
            name='expires_at',
            field=models.DateTimeField(
                db_index=True,
                default=recursos.models.expira_default
            ),
        ),
    ]
