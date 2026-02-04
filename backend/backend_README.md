# Backend - Django REST API

Quick reference for backend development. See [main README](../README.md) for project overview.

## Quick Start

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements/development.txt
cp .env.example .env

# Database
createdb clover_db
python manage.py migrate

# Run
python manage.py createsuperuser
python manage.py runserver
```

API: http://localhost:8000/api/v1/
Admin: http://localhost:8000/admin/

## Project Structure

```
backend/
├── config/              # Django settings (base, dev, prod)
├── apps/
│   └── accounts/       # User authentication & management
├── utils/              # Shared utilities
├── requirements/       # Dependencies
└── manage.py
```

## Common Commands

**Development:**
```bash
python manage.py runserver          # Start dev server
python manage.py shell             # Django shell
python manage.py makemigrations    # Create migrations
python manage.py migrate           # Apply migrations
```

**Testing:**
```bash
pytest                              # Run tests
pytest --cov=apps                  # With coverage
```

**Code Quality:**
```bash
black .                             # Format code
isort .                            # Sort imports
flake8                             # Check style
```

## API Endpoints

See [django_backend_design.md](../django_backend_design.md) for complete API documentation.

### Authentication
- `POST /api/v1/auth/register/` - Register
- `POST /api/v1/auth/login/` - Login
- `POST /api/v1/auth/logout/` - Logout
- `POST /api/v1/auth/token/refresh/` - Refresh token

### Profile
- `GET /api/v1/auth/profile/` - Get profile
- `PUT /api/v1/auth/profile/` - Update profile
- `POST /api/v1/auth/password/change/` - Change password

### Admin Only
- `GET /api/v1/auth/users/` - List users
- `GET/PUT/DELETE /api/v1/auth/users/{id}/` - Manage user

## Environment Variables

Required in `.env`:

```bash
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=clover_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```

## Tech Stack

- Django 5.0
- Django REST Framework 3.14
- PostgreSQL 14+
- JWT Authentication
- Python 3.10+

## Documentation

- **[Main README](../README.md)** - Project overview & quick start
- **[Architecture Doc](../django_backend_design.md)** - Complete system design
- **[Workflow](../workflow.md)** - Project milestones
