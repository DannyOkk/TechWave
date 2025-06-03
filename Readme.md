# 🌐 TechWave - API de Marketplace y Administración de Usuarios

Un sistema completo de **marketplace** y **gestión de usuarios** construido con Django REST Framework. Proporciona funcionalidades robustas para e-commerce, incluyendo gestión de productos, pedidos, pagos, envíos y administración de usuarios con roles específicos.

---

## 🚀 Características Principales

### 👥 Gestión de Usuarios
- **Roles de usuario**: Admin, Operador, Cliente
- **Autenticación JWT** con tokens de acceso y refresh
- **Sistema de permisos** granular por rol
- **Registro y login** de usuarios
- **Cambio de roles** (solo administradores)

### 🛍️ Marketplace
- **Gestión de productos** con categorías y stock
- **Carrito de compras** dinámico
- **Sistema de pedidos** con estados (pendiente, procesando, pagado, enviado, entregado, cancelado)
- **Procesamiento de pagos** (tarjeta, PayPal, transferencia)
- **Gestión de envíos** con tracking
- **Permisos específicos** por tipo de usuario

---

## 🗂️ Estructura del Proyecto

```
TechWave/
├── TechWave/                   # Configuración principal Django
│   ├── settings.py             # Configuraciones globales
│   ├── urls.py                 # Enrutamiento principal
│   ├── permissions.py          # Clases de permisos personalizadas
│   └── wsgi.py/asgi.py        # Configuración de despliegue
│
├── account_admin/              # App de administración de usuarios
│   ├── models.py              # Modelo de usuario personalizado
│   ├── serializer.py          # Serializadores de usuario
│   ├── views.py               # Vistas de autenticación y gestión
│   ├── urls.py                # Endpoints de usuarios
│   └── tests/                 # Tests unitarios
│
├── market/                     # App del marketplace
│   ├── models.py              # Productos, pedidos, pagos, envíos
│   ├── serializer.py          # Serializadores del marketplace
│   ├── views.py               # Lógica de negocio del market
│   ├── urls.py                # Endpoints del marketplace
│   └── tests/                 # Tests completos del sistema
│
└── manage.py                   # Script de gestión Django
```

---

## ⚙️ Stack Tecnológico

- **Backend**: Python 3.13+ con Django 5.1+
- **API**: Django REST Framework
- **Autenticación**: JWT (django-rest-framework-simplejwt)
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Testing**: Django TestCase y APITestCase
- **Documentación**: drf-spectacular (OpenAPI/Swagger)

---

## 🔧 Instalación y Configuración

### 1. Clona el repositorio
```bash
git clone https://github.com/tu-usuario/TechWave.git
cd TechWave
```

### 2. Configura el entorno virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instala las dependencias
```bash
pip install -r requirements.txt
```

### 4. Configura la base de datos
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Crea un superusuario (opcional)
```bash
python manage.py createsuperuser
```

### 6. Inicia el servidor de desarrollo
```bash
python manage.py runserver
```

La API estará disponible en `http://localhost:8000/`

---

## 📖 Endpoints Principales

### Autenticación
- `POST /api/login/` - Inicio de sesión
- `POST /api/logout/` - Cerrar sesión
- `POST /api/create-user/` - Registro de usuario
- `PUT /api/change-role/{user_id}/` - Cambiar rol (admin)

### Marketplace
- `GET /api/products/` - Listar productos
- `POST /api/products/{id}/add-to-cart/` - Agregar al carrito
- `GET /api/orders/` - Gestionar pedidos
- `POST /api/orders/{id}/cancel/` - Cancelar pedido
- `GET /api/payments/` - Gestionar pagos
- `POST /api/payments/{id}/complete-payment/` - Completar pago
- `GET /api/shipments/` - Gestionar envíos
- `POST /api/shipments/{id}/update-status/` - Actualizar estado de envío

### Documentación
- `GET /api/schema/` - Esquema OpenAPI
- `GET /api/docs/` - Documentación Swagger UI

---

## 🧪 Testing

### Ejecutar todos los tests
```bash
python manage.py test
```

### Ejecutar tests específicos
```bash
# Tests de usuarios
python manage.py test account_admin.tests

# Tests del marketplace
python manage.py test market.tests

# Test específico
python manage.py test market.tests.test_views.TestViews.test_order_create
```

### Cobertura de tests
El proyecto incluye tests completos para:
- ✅ Autenticación y autorización
- ✅ CRUD de productos y categorías
- ✅ Gestión del carrito de compras
- ✅ Flujo completo de pedidos
- ✅ Procesamiento de pagos
- ✅ Sistema de envíos
- ✅ Permisos por rol de usuario

---

## 🔐 Sistema de Permisos

### Roles de Usuario
- **Admin**: Acceso completo a todas las funcionalidades
- **Operador**: Gestión de pedidos, envíos y productos
- **Cliente**: Compras, visualización de sus pedidos y tracking

### Permisos Específicos
- **Productos**: Lectura para todos, escritura para admin/operador
- **Pedidos**: Clientes ven solo los suyos, admin/operador ven todos
- **Pagos**: Completar pagos solo admin/operador
- **Envíos**: Actualizar estado solo admin/operador
- **Usuarios**: Cambiar roles solo admin

---

## 🚀 Despliegue

### Variables de Entorno
Crea un archivo `.env` con:
```env
SECRET_KEY=tu-clave-secreta-muy-segura
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
DATABASE_URL=postgresql://usuario:password@host:port/basedatos
```

### Docker (opcional)
```bash
# Construir imagen
docker build -t techwave-api .

# Ejecutar contenedor
docker run -p 8000:8000 techwave-api
```

---

## 🤝 Contribución

1. **Fork** el repositorio
2. Crea una rama para tu feature:
   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```
3. Realiza tus cambios y agrega tests
4. Asegúrate de que todos los tests pasen:
   ```bash
   python manage.py test
   ```
5. Haz commit de tus cambios:
   ```bash
   git commit -m "feat: descripción de la nueva funcionalidad"
   ```
6. Push a tu rama:
   ```bash
   git push origin feature/nueva-funcionalidad
   ```
7. Abre un **Pull Request**

---

## 📋 Estado del Proyecto

- ✅ **Estable**: API de usuarios y autenticación
- ✅ **Estable**: Sistema de productos y categorías
- ✅ **Estable**: Gestión de pedidos y carrito
- ✅ **Estable**: Sistema de pagos
- ✅ **Estable**: Gestión de envíos y tracking
- ⚠️ **En desarrollo**: Panel de administración web
- 📋 **Planificado**: Notificaciones en tiempo real
- 📋 **Planificado**: Sistema de reseñas

---
**TechWave** - Construyendo el futuro del comercio digital 🚀
