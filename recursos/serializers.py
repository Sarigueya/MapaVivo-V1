from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Recurso, Organizacion


# ── AUTH ───────────────────────────────────────────────────────────────────────

class RegistroSerializer(serializers.Serializer):
    username    = serializers.CharField(min_length=4, max_length=50)
    email       = serializers.EmailField()
    password    = serializers.CharField(min_length=8, write_only=True)
    nombre_org  = serializers.CharField(min_length=3, max_length=200)
    descripcion = serializers.CharField(min_length=20)
    direccion   = serializers.CharField(min_length=5, max_length=300)
    telefono    = serializers.CharField(required=False, allow_blank=True, default='')
    sitio_web   = serializers.URLField(required=False, allow_blank=True, default='')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Ese nombre de usuario ya está en uso.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Ya existe una cuenta con ese correo.')
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username  = validated_data['username'],
            email     = validated_data['email'],
            password  = validated_data['password'],
            is_active = False,
        )
        Organizacion.objects.create(
            usuario     = user,
            nombre_org  = validated_data['nombre_org'],
            descripcion = validated_data['descripcion'],
            direccion   = validated_data['direccion'],
            telefono    = validated_data.get('telefono', ''),
            sitio_web   = validated_data.get('sitio_web', ''),
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class OrganizacionInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Organizacion
        fields = ['nombre_org', 'estado', 'descripcion', 'direccion']


class UsuarioSerializer(serializers.ModelSerializer):
    organizacion = OrganizacionInfoSerializer(read_only=True)

    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'organizacion']


# ── RECURSOS ───────────────────────────────────────────────────────────────────

class RecursoSerializer(serializers.ModelSerializer):
    # Estado calculado dinámicamente — solo lectura
    estado            = serializers.SerializerMethodField()
    creado_por_nombre = serializers.SerializerMethodField()
    creado_por_id     = serializers.SerializerMethodField()
    horario_texto     = serializers.SerializerMethodField()

    class Meta:
        model  = Recurso
        fields = [
            'id', 'nombre', 'tipo', 'descripcion', 'direccion',
            'lat', 'lng', 'requisitos',
            # Horario
            'dias_atencion', 'hora_apertura', 'hora_cierre', 'sin_horario',
            # Estado
            'estado', 'sin_stock_hoy', 'horario_texto',
            # Meta
            'updated_at', 'created_at', 'creado_por_nombre','creado_por_id',
        ]
        read_only_fields = [
            'id', 'updated_at', 'created_at',
            'estado', 'creado_por_nombre','creado_por_id', 'horario_texto'
        ]

    def get_creado_por_id(self, obj):  # Para mostrar el ID del usuario que creó el recurso
        return obj.creado_por_id if obj.creado_por else None

    def get_estado(self, obj):
        return obj.calcular_estado()

    def get_creado_por_nombre(self, obj):
        if obj.creado_por:
            try:
                return obj.creado_por.organizacion.nombre_org
            except Exception:
                return obj.creado_por.username
        return None

    def get_horario_texto(self, obj):
        """Texto legible del horario para mostrar en el mapa."""
        if obj.sin_horario or not obj.hora_apertura or not obj.hora_cierre:
            return 'Horario variable'
        dias_map = {
            'lun':'Lun','mar':'Mar','mie':'Mié',
            'jue':'Jue','vie':'Vie','sab':'Sáb','dom':'Dom'
        }
        dias = [d.strip() for d in obj.dias_atencion.split(',') if d.strip()]
        dias_texto = ' · '.join([dias_map.get(d, d) for d in dias])
        return f"{dias_texto} · {obj.hora_apertura.strftime('%H:%M')} – {obj.hora_cierre.strftime('%H:%M')}"

    def validate_tipo(self, value):
        tipos = [t[0] for t in Recurso.TIPO_CHOICES]
        if value not in tipos:
            raise serializers.ValidationError(f'Tipo inválido. Opciones: {", ".join(tipos)}')
        return value

    def validate(self, data):
        # Si tiene horario, los dos campos son obligatorios
        sin_horario   = data.get('sin_horario', False)
        hora_apertura = data.get('hora_apertura')
        hora_cierre   = data.get('hora_cierre')

        if not sin_horario:
            if hora_apertura and hora_cierre:
                if hora_apertura >= hora_cierre:
                    raise serializers.ValidationError(
                        'La hora de apertura debe ser anterior a la hora de cierre.'
                    )
        return data

    def validate_lat(self, value):
        if not -90 <= value <= 90:
            raise serializers.ValidationError('Latitud debe estar entre -90 y 90')
        return value

    def validate_lng(self, value):
        if not -180 <= value <= 180:
            raise serializers.ValidationError('Longitud debe estar entre -180 y 180')
        return value

class RecursoUpdateSerializer(serializers.ModelSerializer):
    """Para actualizar descripción, horario o activar sin_stock."""
    class Meta:
        model = Recurso
        fields = [
            'nombre', 'descripcion', 'requisitos', 'direccion',  
            'dias_atencion', 'hora_apertura', 'hora_cierre', 'sin_horario',
        ]