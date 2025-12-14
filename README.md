# 🎫 Helpdesk System

Sistema de Mesa de Ayuda con tickets, notificaciones en tiempo real, y emails asíncronos.

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Características

- **API REST** con Django REST Framework
- **Autenticación JWT** (access token 1h, refresh token 7d)
- **WebSockets** para notificaciones en tiempo real
- **Emails asíncronos** con Celery y templates HTML
- **Cache con Redis** (TTL 5 minutos)
- **Rate Limiting** (100 req/min usuarios, 20 req/min anónimos)
- **Roles de usuario**: Customer y Agent
- **Paginación** (20 items por página)

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| Backend | Django 5.2, Django REST Framework |
| Base de Datos | PostgreSQL 16 |
| Cache & Broker | Redis |
| Tasks Asíncronos | Celery |
| WebSockets | Django Channels + Daphne |
| Contenedores | Docker & Docker Compose |

## 🚀 Quick Start

### Requisitos Previos

- Docker y Docker Compose
- Git

### Instalación
```bash
# Clonar el repositorio
git clone https://github.com/daniel-caso-github/helpdesk_system.git
cd helpdesk_system

# Levantar todos los servicios
docker compose -f docker-compose.local.yml up -d --build

# Crear superusuario
docker compose -f docker-compose.local.yml run --rm django python manage.py createsuperuser

# Generar datos de prueba (opcional)
docker compose -f docker-compose.local.yml run --rm django python manage.py generate_fake_data --tickets=1000
```

### URLs Disponibles

| Servicio | URL |
|----------|-----|
| API | http://localhost:8000/api/ |
| Swagger UI | http://localhost:8000/api/docs/ |
| Admin | http://localhost:8000/admin/ |
| Mailpit (emails) | http://localhost:8025 |
| Flower (Celery) | http://localhost:5555 |

## 📚 API Endpoints

### Autenticación
```bash
# Obtener tokens JWT
POST /api/auth/token/
{
    "username": "usuario",
    "password": "contraseña"
}

# Refrescar token
POST /api/auth/token/refresh/
{
    "refresh": "eyJ..."
}
```

### Tickets
```bash
# Listar tickets (paginado)
GET /api/tickets/
Authorization: Bearer <token>

# Crear ticket
POST /api/tickets/
{
    "title": "Problema con el sistema",
    "description": "Descripción detallada...",
    "priority": "high"  # low, medium, high, urgent
}

# Ver ticket con comentarios
GET /api/tickets/{id}/

# Actualizar ticket (solo agents)
PATCH /api/tickets/{id}/
{
    "status": "in_progress",  # open, in_progress, resolved, closed
    "assigned_to": 5
}

# Filtrar tickets
GET /api/tickets/?status=open&priority=urgent&search=error
```

### Comentarios
```bash
# Listar comentarios de un ticket
GET /api/comments/?ticket={id}

# Crear comentario
POST /api/comments/
{
    "ticket": 1,
    "content": "Contenido del comentario"
}
```

## 🔌 WebSockets

### Conexión
```javascript
const token = "eyJ...";  // JWT access token
const ws = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${token}`);

ws.onopen = () => console.log("Conectado");
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Notificación:", data);
};
```

### Eventos

**ticket_created** (solo agents):
```json
{
    "type": "ticket_created",
    "ticket": {
        "id": 1,
        "title": "Nuevo ticket",
        "priority": "high",
        "status": "open",
        "created_by": "customer1"
    },
    "message": "New ticket #1: Nuevo ticket"
}
```

**status_changed** (creador del ticket):
```json
{
    "type": "status_changed",
    "ticket": {
        "id": 1,
        "title": "Mi ticket",
        "old_status": "open",
        "new_status": "in_progress"
    },
    "message": "Ticket #1 status changed to In Progress"
}
```

**comment_added** (creador y asignado):
```json
{
    "type": "comment_added",
    "ticket": {"id": 1, "title": "Mi ticket"},
    "comment": {
        "id": 5,
        "author": "agent1",
        "content": "Estamos trabajando en esto..."
    },
    "message": "New comment on ticket #1"
}
```

## 👥 Roles y Permisos

| Acción | Customer | Agent |
|--------|----------|-------|
| Crear tickets | ✅ | ✅ |
| Ver sus tickets | ✅ | ✅ (todos) |
| Comentar en sus tickets | ✅ | ✅ (todos) |
| Cambiar estado | ❌ | ✅ |
| Asignar tickets | ❌ | ✅ |
| Recibir notificación de nuevos tickets | ❌ | ✅ |

## 🧪 Generación de Datos de Prueba
```bash
# Generar 10,000 tickets con 50,000 comentarios (~10 segundos)
docker compose -f docker-compose.local.yml run --rm django \
    python manage.py generate_fake_data \
    --tickets=10000 \
    --comments-per-ticket=5 \
    --customers=50 \
    --agents=10

# Usuarios generados: customer_1, customer_2, ... agent_1, agent_2, ...
# Password para todos: testpass123
```

## ⚙️ Variables de Entorno

Las variables se configuran en `.envs/.local/`:

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Clave secreta Django | Auto-generada |
| `DATABASE_URL` | URL de PostgreSQL | postgres://... |
| `REDIS_URL` | URL de Redis | redis://redis:6379/0 |
| `CELERY_BROKER_URL` | URL del broker Celery | redis://redis:6379/0 |

## 🏗️ Arquitectura
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Cliente   │────▶│   Daphne    │────▶│   Django    │
│  (Browser)  │     │   (ASGI)    │     │   (App)     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           │                   ▼
                           │            ┌─────────────┐
                           │            │ PostgreSQL  │
                           │            └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    Redis    │◀───▶│   Celery    │
                    │(Cache/WS/Q) │     │  (Worker)   │
                    └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │   Mailpit   │
                                        │   (SMTP)    │
                                        └─────────────┘
```

## 🔧 Comandos Útiles
```bash
# Ver logs
docker compose -f docker-compose.local.yml logs -f django
docker compose -f docker-compose.local.yml logs -f celeryworker

# Ejecutar shell Django
docker compose -f docker-compose.local.yml run --rm django python manage.py shell

# Ejecutar migraciones
docker compose -f docker-compose.local.yml run --rm django python manage.py migrate

# Limpiar cache Redis
docker compose -f docker-compose.local.yml exec redis redis-cli FLUSHALL

# Ejecutar tests
docker compose -f docker-compose.local.yml run --rm django pytest

# Ejecutar pre-commit
pre-commit run --all-files
```

## 📊 Optimizaciones Implementadas

1. **Query Optimization**
   - `select_related()` para evitar N+1 queries
   - `annotate()` para campos calculados (comments_count, last_comment_at)

2. **Cache con Redis**
   - TTL de 5 minutos para listados
   - Invalidación automática en create/update/delete

3. **Bulk Operations**
   - `bulk_create()` con batch_size=1000
   - Generación de 10k tickets en ~10 segundos

4. **Rate Limiting**
   - 100 requests/minuto para usuarios autenticados
   - 20 requests/minuto para anónimos
   - Respuesta HTTP 429 cuando se excede

## 📝 Decisiones Técnicas

| Decisión | Justificación |
|----------|---------------|
| JWT sobre Sessions | API stateless, mejor para microservicios |
| Redis para todo | Cache, Celery broker, Channel layers - simplicidad |
| Daphne sobre Gunicorn | Soporte nativo ASGI para WebSockets |
| bulk_create con batches | Performance en inserciones masivas |
| Signals para notificaciones | Desacoplamiento entre modelos y notificaciones |

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para más detalles.

## 👨‍💻 Autor

Daniel Caso Quintanilla - [daniel.caso.quintanilla@gmail.com](mailto:daniel.caso.quintanilla@gmail.com)
