from django.contrib import admin
from django.utils.html import format_html
from .models import Recurso, Organizacion


# ── ORGANIZACIÓN ───────────────────────────────────────────────────────────────

@admin.register(Organizacion)
class OrganizacionAdmin(admin.ModelAdmin):
    list_display  = ['nombre_org', 'usuario', 'estado_coloreado', 'telefono', 'creada_en']
    list_filter   = ['estado']
    search_fields = ['nombre_org', 'usuario__username', 'usuario__email']
    readonly_fields = ['creada_en', 'actualizada_en', 'usuario']
    ordering      = ['-creada_en']

    fieldsets = [
        ('Datos de la organización', {
            'fields': ['nombre_org', 'descripcion', 'direccion', 'telefono', 'sitio_web']
        }),
        ('Cuenta', {
            'fields': ['usuario', 'creada_en', 'actualizada_en']
        }),
        ('Revisión administrativa', {
            'fields': ['estado', 'nota_admin'],
            'description': 'Cambiá el estado a "Aprobada" para que la organización pueda iniciar sesión.',
        }),
    ]

    actions = ['aprobar_seleccionadas', 'rechazar_seleccionadas']

    def estado_coloreado(self, obj):
        colores = {
            'pendiente': '#b06010',
            'aprobada':  '#2d7a4f',
            'rechazada': '#c94040',
        }
        color = colores.get(obj.estado, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_coloreado.short_description = 'Estado'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.estado == 'aprobada':
            obj.usuario.is_active = True
            obj.usuario.save(update_fields=['is_active'])
        elif obj.estado == 'rechazada':
            obj.usuario.is_active = False
            obj.usuario.save(update_fields=['is_active'])

    @admin.action(description='Aprobar organizaciones seleccionadas')
    def aprobar_seleccionadas(self, request, queryset):
        for org in queryset:
            org.estado = 'aprobada'
            org.save()
            org.usuario.is_active = True
            org.usuario.save(update_fields=['is_active'])
        self.message_user(request, f'{queryset.count()} organización(es) aprobada(s).')

    @admin.action(description='Rechazar organizaciones seleccionadas')
    def rechazar_seleccionadas(self, request, queryset):
        for org in queryset:
            org.estado = 'rechazada'
            org.save()
            org.usuario.is_active = False
            org.usuario.save(update_fields=['is_active'])
        self.message_user(request, f'{queryset.count()} organización(es) rechazada(s).')


# ── RECURSO ────────────────────────────────────────────────────────────────────

@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    # 'estado' es propiedad calculada, no campo de BD — no va en list_filter ni list_editable
    list_display   = ['nombre', 'tipo', 'estado_actual', 'sin_stock_hoy',
                      'creado_por', 'hora_apertura', 'hora_cierre', 'updated_at']
    list_filter    = ['tipo', 'sin_stock_hoy']
    search_fields  = ['nombre', 'direccion', 'creado_por__username']
    readonly_fields = ['created_at', 'updated_at', 'creado_por', 'estado_actual']
    ordering       = ['-updated_at']

    fieldsets = [
        ('Datos básicos', {
            'fields': ['nombre', 'tipo', 'descripcion', 'direccion', 'requisitos', 'creado_por']
        }),
        ('Ubicación', {
            'fields': ['lat', 'lng']
        }),
        ('Horario', {
            'fields': ['sin_horario', 'dias_atencion', 'hora_apertura', 'hora_cierre'],
            'description': 'Días separados por coma: lun,mar,mie,jue,vie,sab,dom'
        }),
        ('Estado', {
            'fields': ['estado_actual', 'sin_stock_hoy', 'sin_stock_fecha'],
            'description': 'El estado se calcula automáticamente según el horario. '
                           'Sin stock hoy es la única excepción manual.'
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def estado_actual(self, obj):
        estado = obj.calcular_estado()
        colores = {
            'open':   ('#2d7a4f', 'Abierto'),
            'soon':   ('#b06010', 'Cierra pronto'),
            'closed': ('#c94040', 'Cerrado'),
        }
        color, texto = colores.get(estado, ('#666', estado))
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>', color, texto
        )
    estado_actual.short_description = 'Estado ahora'
