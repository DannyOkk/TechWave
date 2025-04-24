# 🌐 TechWave - Módulo de Administración de Usuarios y Marketplace

Este proyecto es un módulo del ecosistema **TechWave**, orientado a ofrecer funcionalidades de **gestión de usuarios** y de **mercado digital (marketplace)**, implementadas con **Django** y **Django REST Framework**. Está pensado para ser mantenible, escalable y fácilmente integrable dentro de una arquitectura mayor.

---

## 🗂️ Estructura General

```
├── TechWave/               # Proyecto Django (configuraciones globales)
│   ├── settings.py         # Configuración general del proyecto
│   ├── urls.py             # Enrutamiento global
│   └── wsgi.py/asgi.py     # Despliegue
│
├── account_admin/          # App para gestión de usuarios
│   ├── admin.py            # Registro de modelos en el admin
│   ├── models.py           # Definición de modelos personalizados
│   ├── serializer.py       # Serializadores de DRF
│   ├── urls.py             # Rutas de API
│   └── views.py            # Vistas basadas en API
│
├── market/                 # App para el marketplace
│   ├── models.py           # Productos, categorías, etc.
│   ├── serializer.py       # Serializadores DRF
│   ├── views.py            # Lógica de vistas para APIs del market
│   └── urls.py             # Enrutamiento específico
│
├── Teoria/                 # Documentación técnica
│   └── Tecnologías y Conceptos Clave.md
│
├── manage.py               # Script de gestión Django
└── .gitignore
```

---

## ⚙️ Stack Tecnológico

- **Python 3.11+**
- **Django 4.x**
- **Django REST Framework**
- **SQLite** (base de datos por defecto para desarrollo)
- Soporte para despliegue con **WSGI/ASGI**

---

## ▶️ Ejecución Local

### 1. Clona el repositorio

```bash
git clone <url>
cd TechWave-Feature-UserAdmin
```

### 2. Crea y activa el entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instala las dependencias

```bash
pip install -r requirements.txt
```

### 4. Aplica migraciones

```bash
python manage.py migrate
```

### 5. Inicia el servidor

```bash
python manage.py runserver
```

---

## 🧪 Pruebas

Para ejecutar los tests:

```bash
python manage.py test
```

Puedes añadir más tests en los archivos `tests.py` dentro de cada app.

---

## 📄 Documentación Adicional

Revisa la carpeta `Teoria/` para entender los fundamentos técnicos y decisiones arquitectónicas detrás de este módulo.

---

## 🤝 Contribución

1. Haz un fork del repositorio.
2. Crea una rama:
   ```bash
   git checkout -b feature/nombre
   ```
3. Realiza tus cambios y haz commits.
4. Haz push a tu rama:
   ```bash
   git push origin feature/nombre
   ```
5. Abre un Pull Request.
