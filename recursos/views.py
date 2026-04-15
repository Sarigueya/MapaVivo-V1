import random
import string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Recurso, Organizacion
from .serializers import (
    RecursoSerializer, RecursoUpdateSerializer,
    RegistroSerializer, LoginSerializer, UsuarioSerializer
)


def es_org_aprobada(user):
    if not user.is_authenticated:
        return False
    try:
        return user.organizacion.esta_aprobada
    except Exception:
        return False


def generar_password_temporal(longitud=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=longitud))


# ── AUTH ───────────────────────────────────────────────────────────────────────

class RegistroView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = RegistroSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(
                {'mensaje': 'Solicitud enviada. Un administrador revisará tu cuenta en breve.'},
                status=status.HTTP_201_CREATED
            )
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)

        user = authenticate(
            request,
            username=ser.validated_data['username'],
            password=ser.validated_data['password'],
        )

        if user is None:
            try:
                u = User.objects.get(username=ser.validated_data['username'])
                if not u.is_active:
                    try:
                        estado = u.organizacion.get_estado_display()
                    except Exception:
                        estado = 'pendiente'
                    return Response(
                        {'error': f'Tu cuenta está en estado: {estado}. Esperá la aprobación del administrador.'},
                        status=403
                    )
            except User.DoesNotExist:
                pass
            return Response({'error': 'Usuario o contraseña incorrectos.'}, status=401)

        login(request, user)
        return Response(UsuarioSerializer(user).data)


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'mensaje': 'Sesión cerrada.'})


class MiPerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = UsuarioSerializer(request.user).data
        data['is_superuser'] = request.user.is_superuser
        return Response(data)


class ActualizarOrganizacionView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
            org = request.user.organizacion
        except Exception:
            return Response({'error': 'No tenés una organización asociada.'}, status=400)
        for campo in ['nombre_org', 'descripcion', 'direccion', 'telefono', 'sitio_web']:
            if campo in request.data:
                setattr(org, campo, request.data[campo])
        org.save()
        return Response({'mensaje': 'Datos actualizados correctamente.'})


class CambiarPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        actual = request.data.get('password_actual', '')
        nueva  = request.data.get('password_nueva', '')
        if not actual or not nueva:
            return Response({'error': 'Completá ambos campos.'}, status=400)
        if len(nueva) < 8:
            return Response({'error': 'La nueva contraseña debe tener al menos 8 caracteres.'}, status=400)
        if not request.user.check_password(actual):
            return Response({'error': 'La contraseña actual es incorrecta.'}, status=400)
        request.user.set_password(nueva)
        request.user.save()
        update_session_auth_hash(request, request.user)
        return Response({'mensaje': 'Contraseña cambiada correctamente.'})


# ── ADMIN ──────────────────────────────────────────────────────────────────────

class AdminOrganizacionesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Sin permiso.'}, status=403)
        orgs = Organizacion.objects.select_related('usuario').order_by('-creada_en')
        data = [{
            'id': o.id, 'nombre_org': o.nombre_org, 'descripcion': o.descripcion,
            'direccion': o.direccion, 'telefono': o.telefono, 'sitio_web': o.sitio_web,
            'estado': o.estado, 'username': o.usuario.username,
            'email': o.usuario.email, 'creada_en': o.creada_en.isoformat(),
            'is_active': o.usuario.is_active,
        } for o in orgs]
        return Response(data)


class AdminOrganizacionDetalleView(APIView):
    permission_classes = [IsAuthenticated]

    def _check(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Sin permiso.'}, status=403)

    def get(self, request, pk):
        if e := self._check(request): return e
        org = get_object_or_404(Organizacion, pk=pk)
        return Response({
            'id': org.id, 'nombre_org': org.nombre_org, 'descripcion': org.descripcion,
            'direccion': org.direccion, 'telefono': org.telefono, 'sitio_web': org.sitio_web,
            'estado': org.estado, 'username': org.usuario.username,
            'email': org.usuario.email, 'creada_en': org.creada_en.isoformat(),
        })

    def patch(self, request, pk):
        if e := self._check(request): return e
        org    = get_object_or_404(Organizacion, pk=pk)
        estado = request.data.get('estado')
        if estado in ['pendiente', 'aprobada', 'rechazada']:
            org.estado = estado
            org.save()
            org.usuario.is_active = (estado == 'aprobada')
            org.usuario.save(update_fields=['is_active'])
        return Response({'mensaje': 'Estado actualizado.', 'estado': org.estado})


class AdminResetPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Sin permiso.'}, status=403)
        org      = get_object_or_404(Organizacion, pk=pk)
        nueva    = generar_password_temporal()
        org.usuario.set_password(nueva)
        org.usuario.save()
        return Response({'password_temporal': nueva})


# ── RECURSOS ───────────────────────────────────────────────────────────────────

class RecursoListCreate(APIView):

    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAuthenticated()]

    def get(self, request):
        qs     = Recurso.objects.all()
        tipo   = request.query_params.get('tipo')
        if tipo: qs = qs.filter(tipo=tipo)
        # Serializar y agregar estado calculado
        data = RecursoSerializer(qs, many=True).data
        return Response(data)

    def post(self, request):
        if not es_org_aprobada(request.user):
            return Response(
                {'error': 'Solo las organizaciones verificadas pueden agregar recursos.'},
                status=403
            )
        ser = RecursoSerializer(data=request.data)
        if ser.is_valid():
            ser.save(creado_por=request.user)
            return Response(ser.data, status=201)
        return Response(ser.errors, status=400)


# Vista para que un usuario vea solo sus recursos (sin importar el estado) --> por probar
class MisRecursosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        recursos = Recurso.objects.filter(creado_por=request.user)
        return Response(RecursoSerializer(recursos, many=True).data)

class RecursoDetail(APIView):
    permission_classes = [IsAuthenticated]

    def _puede(self, request, recurso):
        if request.user.is_superuser: return True
        return recurso.creado_por == request.user and es_org_aprobada(request.user)

    def patch(self, request, pk):
        recurso = get_object_or_404(Recurso, pk=pk)
        if not self._puede(request, recurso):
            return Response({'error': 'Sin permiso.'}, status=403)
        ser = RecursoUpdateSerializer(recurso, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(RecursoSerializer(recurso).data)
        return Response(ser.errors, status=400)

    def delete(self, request, pk):
        recurso = get_object_or_404(Recurso, pk=pk)
        if not self._puede(request, recurso):
            return Response({'error': 'Sin permiso.'}, status=403)
        recurso.delete()
        return Response(status=204)


class RecursoSinStockView(APIView):
    """
    POST /api/recursos/<id>/sin-stock/    → activa sin stock hoy
    DELETE /api/recursos/<id>/sin-stock/  → desactiva (hay stock de nuevo)
    """
    permission_classes = [IsAuthenticated]

    def _puede(self, request, recurso):
        if request.user.is_superuser: return True
        return recurso.creado_por == request.user and es_org_aprobada(request.user)

    def post(self, request, pk):
        recurso = get_object_or_404(Recurso, pk=pk)
        if not self._puede(request, recurso):
            return Response({'error': 'Sin permiso.'}, status=403)
        recurso.activar_sin_stock()
        return Response({'estado': recurso.calcular_estado(), 'sin_stock_hoy': True})

    def delete(self, request, pk):
        recurso = get_object_or_404(Recurso, pk=pk)
        if not self._puede(request, recurso):
            return Response({'error': 'Sin permiso.'}, status=403)
        recurso.desactivar_sin_stock()
        return Response({'estado': recurso.calcular_estado(), 'sin_stock_hoy': False})


class HealthCheck(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'status': 'ok',
            'timestamp': timezone.now(),
            'autenticado': request.user.is_authenticated,
        })

# Vistas para PQRs (Peticiones, Quejas y Reclamos)
class PQRCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        datos = request.data
        if not datos.get('nombre') or not datos.get('email') or not datos.get('mensaje'):
            return Response({'error': 'Nombre, email y mensaje son obligatorios.'}, status=400)
        pqr = PQR.objects.create(
            nombre  = datos['nombre'],
            email   = datos['email'],
            tipo    = datos.get('tipo', 'peticion'),
            mensaje = datos['mensaje'],
            recurso_id = datos.get('recurso_id'),
        )
        return Response({'mensaje': 'PQR enviada correctamente.', 'id': pqr.id}, status=201)


class AdminPQRView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Sin permiso.'}, status=403)
        pqrs = PQR.objects.select_related('recurso').all()
        data = [{
            'id': p.id, 'nombre': p.nombre, 'email': p.email,
            'tipo': p.tipo, 'mensaje': p.mensaje, 'estado': p.estado,
            'recurso': p.recurso.nombre if p.recurso else None,
            'creado_en': p.creado_en.isoformat(),
        } for p in pqrs]
        return Response(data)

    def patch(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Sin permiso.'}, status=403)
        pqr = get_object_or_404(PQR, pk=pk)
        if 'estado' in request.data:
            pqr.estado = request.data['estado']
            pqr.save()
        return Response({'mensaje': 'Estado actualizado.'})