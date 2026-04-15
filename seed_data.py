"""
Script para cargar datos de prueba en la base de datos.

Uso:
    python manage.py shell < seed_data.py
  o desde el shell:
    python manage.py shell
    >>> exec(open('seed_data.py').read())
"""
from recursos.models import Recurso

Recurso.objects.all().delete()

Recurso.objects.bulk_create([
    Recurso(
        nombre='Comedor San Martín',
        tipo='comedor',
        descripcion='Almuerzo gratuito de lunes a viernes hasta las 14 hs. Sin turno previo. Capacidad para 80 personas.',
        direccion='Av. San Martín 1240, Villa Crespo',
        lat=-34.5985,
        lng=-58.4390,
        estado='open',
        requisitos='Sin requisitos',
    ),
    Recurso(
        nombre='Banco Alimentario Norte',
        tipo='banco',
        descripcion='Cajas familiares mensuales. Distribución los miércoles de 9 a 12 hs.',
        direccion='Corrientes 3800, Almagro',
        lat=-34.5968,
        lng=-58.4298,
        estado='soon',
        requisitos='DNI + comprobante de domicilio',
    ),
    Recurso(
        nombre='Olla Barrio Esperanza',
        tipo='comedor',
        descripcion='Cena comunitaria todas las noches a las 20 hs. Bienvenidos todos.',
        direccion='Rivadavia 5500, Caballito',
        lat=-34.6056,
        lng=-58.4385,
        estado='open',
        requisitos='Sin requisitos',
    ),
    Recurso(
        nombre='Reparto CABA Norte',
        tipo='reparto',
        descripcion='Distribución de viandas frías. Se reparten hasta agotar stock.',
        direccion='Córdoba 4200, Palermo',
        lat=-34.5893,
        lng=-58.4245,
        estado='open',
        requisitos='Sin requisitos',
    ),
    Recurso(
        nombre='Canastas Solidarias',
        tipo='canasta',
        descripcion='Canastas básicas cada 15 días para familias con menores de edad.',
        direccion='Lavalle 2800, Balvanera',
        lat=-34.6022,
        lng=-58.4097,
        estado='closed',
        requisitos='Familias con menores de edad',
    ),
])

print(f"✓ {Recurso.objects.count()} recursos cargados correctamente.")
