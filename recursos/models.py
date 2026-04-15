from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, time


def expira_default():
    return timezone.now() + timedelta(days=365)  # recursos con horario no expiran en 8h


DIAS_SEMANA = [
    ('lun', 'Lunes'),
    ('mar', 'Martes'),
    ('mie', 'Miércoles'),
    ('jue', 'Jueves'),
    ('vie', 'Viernes'),
    ('sab', 'Sábado'),
    ('dom', 'Domingo'),
]

# Mapeo día Python (0=lunes) → código
DIA_PYTHON_A_CODIGO = {0:'lun', 1:'mar', 2:'mie', 3:'jue', 4:'vie', 5:'sab', 6:'dom'}


class Organizacion(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de revisión'),
        ('aprobada',  'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    usuario        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='organizacion')
    nombre_org     = models.CharField(max_length=200, verbose_name='Nombre de la organización')
    descripcion    = models.TextField(verbose_name='Descripción')
    direccion      = models.CharField(max_length=300, verbose_name='Dirección física')
    telefono       = models.CharField(max_length=30, blank=True, default='')
    sitio_web      = models.URLField(blank=True, default='')
    estado         = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', db_index=True)
    nota_admin     = models.TextField(blank=True, default='')
    creada_en      = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Organización'
        verbose_name_plural = 'Organizaciones'
        ordering = ['-creada_en']

    def __str__(self):
        return f'{self.nombre_org} [{self.get_estado_display()}]'

    @property
    def esta_aprobada(self):
        return self.estado == 'aprobada'


class Recurso(models.Model):
    TIPO_CHOICES = [
        ('comedor', 'Comedor'),
        ('banco',   'Banco de alimentos'),
        ('reparto', 'Reparto'),
        ('canasta', 'Entrega de canastas'),
    ]

    # ── Datos básicos ──────────────────────────────────────
    creado_por  = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recursos'
    )
    nombre      = models.CharField(max_length=200)
    tipo        = models.CharField(max_length=50, choices=TIPO_CHOICES, db_index=True)
    descripcion = models.TextField(blank=True, default='')
    direccion   = models.CharField(max_length=300, blank=True, default='')
    lat         = models.FloatField()
    lng         = models.FloatField()
    requisitos  = models.CharField(max_length=300, blank=True, default='')

    # ── Horario ────────────────────────────────────────────
    # Días como string separado por comas: "lun,mar,mie,jue,vie"
    dias_atencion  = models.CharField(
        max_length=50, blank=True, default='lun,mar,mie,jue,vie',
        help_text='Días separados por coma: lun,mar,mie,jue,vie,sab,dom'
    )
    hora_apertura  = models.TimeField(null=True, blank=True, help_text='Ej: 11:00')
    hora_cierre    = models.TimeField(null=True, blank=True, help_text='Ej: 14:00')
    sin_horario    = models.BooleanField(
        default=False,
        help_text='Marcar si el recurso no tiene horario fijo (disponible siempre o variable)'
    )

    # ── Estado manual de excepción ─────────────────────────
    sin_stock_hoy  = models.BooleanField(
        default=False,
        help_text='La organización lo activa cuando se quedaron sin stock antes del horario'
    )
    sin_stock_fecha = models.DateField(
        null=True, blank=True,
        help_text='Fecha en que se activó sin_stock (para auto-resetear al día siguiente)'
    )

    # ── Timestamps ─────────────────────────────────────────
    updated_at  = models.DateTimeField(auto_now=True)
    expires_at  = models.DateTimeField(default=expira_default, db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Recurso'
        verbose_name_plural = 'Recursos'

    def __str__(self):
        return f'{self.nombre} ({self.get_tipo_display()})'

    # ── Lógica de estado automático ────────────────────────

    def _resetear_sin_stock_si_es_nuevo_dia(self):
        """Si sin_stock_hoy fue activado ayer o antes, lo resetea."""
        if self.sin_stock_hoy and self.sin_stock_fecha:
            hoy = timezone.localdate()
            if self.sin_stock_fecha < hoy:
                self.sin_stock_hoy   = False
                self.sin_stock_fecha = None
                self.save(update_fields=['sin_stock_hoy', 'sin_stock_fecha'])

    def calcular_estado(self):
        """
        Devuelve 'open', 'soon' o 'closed' según el horario actual.
        Prioridad: sin_stock_hoy > fuera de días > fuera de horario > cierra pronto > abierto
        """
        self._resetear_sin_stock_si_es_nuevo_dia()

        # Sin stock manual
        if self.sin_stock_hoy:
            return 'closed'

        # Sin horario fijo → siempre abierto
        if self.sin_horario or not self.hora_apertura or not self.hora_cierre:
            return 'open'

        ahora_local = timezone.localtime(timezone.now())
        dia_actual  = DIA_PYTHON_A_CODIGO[ahora_local.weekday()]
        hora_actual = ahora_local.time()

        # ¿Funciona hoy?
        dias = [d.strip() for d in self.dias_atencion.split(',') if d.strip()]
        if dia_actual not in dias:
            return 'closed'

        apertura = self.hora_apertura
        cierre   = self.hora_cierre

        # Fuera de horario
        if hora_actual < apertura or hora_actual >= cierre:
            return 'closed'

        # ¿Cierra en los próximos 30 minutos?
        from datetime import datetime, timedelta as td
        cierre_dt   = datetime.combine(ahora_local.date(), cierre)
        actual_dt   = datetime.combine(ahora_local.date(), hora_actual)
        minutos_restantes = (cierre_dt - actual_dt).total_seconds() / 60

        if minutos_restantes <= 30:
            return 'soon'

        return 'open'

    @property
    def estado(self):
        """Propiedad dinámica — el estado siempre se calcula en tiempo real."""
        return self.calcular_estado()

    def activar_sin_stock(self):
        self.sin_stock_hoy   = True
        self.sin_stock_fecha = timezone.localdate()
        self.save(update_fields=['sin_stock_hoy', 'sin_stock_fecha'])

    def desactivar_sin_stock(self):
        self.sin_stock_hoy   = False
        self.sin_stock_fecha = None
        self.save(update_fields=['sin_stock_hoy', 'sin_stock_fecha'])

    def renovar(self, horas=8):
        """Mantener compatibilidad — con horario no es necesario pero no rompe nada."""
        pass

# Modelo para PQRs (Peticiones, Quejas y Reclamos)
class PQR(models.Model):
    TIPO_CHOICES = [
        ('peticion', 'Petición'),
        ('queja',    'Queja'),
        ('reclamo',  'Reclamo'),
    ]
    ESTADO_CHOICES = [
        ('nuevo',      'Nuevo'),
        ('en_revision','En revisión'),
        ('resuelto',   'Resuelto'),
    ]
    nombre     = models.CharField(max_length=200)
    email      = models.CharField(max_length=200)
    tipo       = models.CharField(max_length=20, choices=TIPO_CHOICES)
    mensaje    = models.TextField()
    estado     = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='nuevo')
    recurso    = models.ForeignKey(Recurso, on_delete=models.SET_NULL, null=True, blank=True)
    creado_en  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'PQR'