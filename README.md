# Mapa Vivo · Django + MySQL

## Estructura del proyecto

```
mapa-vivo-django/
├── manage.py
├── requirements.txt
├── .env.example          ← copiá como .env y completá
├── mapavivo/             ← configuración Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── recursos/             ← app principal
│   ├── models.py         ← tabla recursos
│   ├── serializers.py    ← validación DRF
│   ├── views.py          ← endpoints API
│   ├── urls.py           ← rutas /api/
│   └── admin.py          ← panel admin
└── frontend/
    └── index.html        ← app del mapa (Leaflet + JS)
```

---

## Paso 1 · MySQL: crear la base de datos

```sql
-- En tu cliente MySQL (Workbench, terminal, DBeaver):
CREATE DATABASE mapavivo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## Paso 2 · Entorno Python

```bash
# Crear entorno virtual
python -m venv venv

# Activar (Mac/Linux)
source venv/bin/activate
# Activar (Windows)
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

> Si mysqlclient falla en Mac: `brew install pkg-config mysql`
> Si falla en Ubuntu: `sudo apt install python3-dev default-libmysqlclient-dev`

---

## Paso 3 · Variables de entorno

```bash
cp .env.example .env
```

Editá `.env` con tus datos reales:

```
SECRET_KEY=una-clave-muy-larga-y-aleatoria
DEBUG=True
DB_NAME=mapavivo
DB_USER=root
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=3306
```

---

## Paso 4 · Migraciones (crea la tabla en MySQL)

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Paso 5 · Crear superusuario (para el admin)

```bash
python manage.py createsuperuser
```

---

## Paso 6 · Levantar el servidor

```bash
python manage.py runserver
```

Abrí en el navegador:

| URL | Qué hace |
|-----|----------|
| http://localhost:8000/ | La app del mapa |
| http://localhost:8000/admin/ | Panel admin Django |
| http://localhost:8000/api/recursos/ | API JSON |
| http://localhost:8000/api/health/ | Healthcheck |

---

## Endpoints de la API

### GET /api/recursos/
Devuelve todos los recursos vigentes (no expirados).

Filtros opcionales:
```
GET /api/recursos/?tipo=comedor
GET /api/recursos/?estado=open
GET /api/recursos/?tipo=banco&estado=open
```

### POST /api/recursos/
Crea un recurso nuevo. Body JSON:
```json
{
  "nombre": "Comedor San Martín",
  "tipo": "comedor",
  "descripcion": "Almuerzo gratuito lunes a viernes",
  "direccion": "Av. San Martín 1240",
  "lat": -34.5985,
  "lng": -58.4390,
  "estado": "open",
  "requisitos": "Sin requisitos"
}
```

### PATCH /api/recursos/<id>/
Actualiza estado o descripción y renueva la expiración:
```json
{ "estado": "closed" }
```

### DELETE /api/recursos/<id>/
Elimina el recurso.

---

## Cargar datos de ejemplo (opcional)

```bash
python manage.py shell
```

```python
from recursos.models import Recurso

Recurso.objects.bulk_create([
    Recurso(nombre='Comedor San Martín', tipo='comedor',
            descripcion='Almuerzo gratuito lunes a viernes, hasta 80 personas.',
            direccion='Av. San Martín 1240', lat=-34.5985, lng=-58.4390, estado='open'),
    Recurso(nombre='Banco Alimentario Norte', tipo='banco',
            descripcion='Cajas familiares mensuales. Traer DNI.',
            direccion='Corrientes 3800', lat=-34.5968, lng=-58.4298, estado='soon'),
    Recurso(nombre='Olla Barrio Esperanza', tipo='comedor',
            descripcion='Cena comunitaria todas las noches a las 20 hs.',
            direccion='Rivadavia 5500', lat=-34.6056, lng=-58.4385, estado='open'),
])
print("Datos cargados")
exit()
```

---

## Preguntas frecuentes

**¿Dónde ajusto la ciudad del mapa?**
En `frontend/index.html`, línea:
```js
map = L.map('map').setView([-34.6037, -58.3816], 13);
//                          ^ lat        ^ lng   ^ zoom
```

**¿Cómo cambio las 8 horas de expiración?**
En `recursos/models.py`, función `expira_default`, cambiá `hours=8`.
En `recursos/views.py`, método `patch`, cambiá `recurso.renovar()` por `recurso.renovar(horas=12)`.

**¿El frontend tiene que estar en Django?**
No es obligatorio. Podés abrir `frontend/index.html` como archivo estático desde cualquier servidor o directamente en el navegador. Solo asegurate de cambiar la constante `API` en el JS:
```js
// Si está separado del servidor Django:
const API = 'http://localhost:8000/api';
```

**¿Cómo despliego en producción?**
Lo más simple para un hackathon: Railway.app o Render.com. Los dos tienen plan gratuito y soportan Django + MySQL. Solo subís el código y configurás las variables de entorno desde el panel.
