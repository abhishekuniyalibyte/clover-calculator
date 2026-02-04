# Clover Payment Analysis Platform

A FinTech platform for analyzing merchant payment processing statements and generating competitive proposals. Built with Django REST Framework backend, designed for iPad-first deployment.

## Quick Overview

The platform helps sales agents:
- Upload and analyze merchant payment statements
- Compare multiple pricing models (Cost-plus, iPlus, Discount rate, Flat)
- Calculate savings across different timeframes
- Generate client-ready PDF proposals

**Current Status:** Milestone 2 - Backend authentication and user management implemented 

## Project Structure

```
clover-project/
├── backend/                     # Django REST API (Active)
│   ├── apps/accounts/          # Authentication & user management
│   ├── config/                 # Django settings
│   └── requirements/           # Python dependencies
├── workflow.md                 # Project milestones (200-240 hours)
├── django_backend_design.md    # Detailed architecture & data models
└── README.md                   # This file
```

## Tech Stack

- **Backend:** Django 5.0 + Django REST Framework
- **Database:** PostgreSQL 14+
- **Authentication:** JWT (djangorestframework-simplejwt)
- **Frontend:** Flutter (planned - Milestone 3)

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+

### Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements/development.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 5. Setup database
createdb clover_db

# 6. Run migrations
python manage.py migrate

# 7. Create admin user
python manage.py createsuperuser

# 8. Start server
python manage.py runserver
```

Access the API at `http://localhost:8000/api/v1/`

## Running the Application

### Terminal 1: Start Backend Server

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python manage.py runserver
```

Keep this terminal running. Server will be available at `http://localhost:8000/`

### Terminal 2: Open Test UI

```bash
cd backend
xdg-open test_ui.html
```

Or manually open `backend/test_ui.html` in your browser.

### Using the Application

1. **Register/Login** at `test_ui.html`
2. **Dashboard** - After login, you'll be redirected to `dashboard.html`
3. **Django Admin** - Access at `http://localhost:8000/admin/`

## API Endpoints (Currently Available)

### Authentication
- `POST /api/v1/auth/register/` - Register user
- `POST /api/v1/auth/login/` - Login (get JWT tokens)
- `POST /api/v1/auth/logout/` - Logout
- `POST /api/v1/auth/token/refresh/` - Refresh access token

### Profile
- `GET /api/v1/auth/profile/` - Get current user
- `PUT /api/v1/auth/profile/` - Update profile
- `POST /api/v1/auth/password/change/` - Change password

### Admin Only
- `GET /api/v1/auth/users/` - List all users
- `GET/PUT/DELETE /api/v1/auth/users/{id}/` - Manage users

### Statements
- `POST /api/v1/statements/upload/` - Upload PDF/image statement
- `POST /api/v1/statements/manual/` - Manual data entry
- `GET /api/v1/statements/` - List user's statements
- `GET /api/v1/statements/{id}/` - Get statement details

## Features

### Implemented
- User registration with validation
- JWT authentication (access + refresh tokens)
- Role-based access control (Admin, Agent)
- User profile management
- Password validation and change
- Custom permissions system
- File upload (PDF/images) for statements
- Manual data entry for statements
- Statement storage and management
- Test UI (login, registration, dashboard)

### Planned 
- Merchant management
- PDF statement upload & extraction
- Pricing engine with multiple models
- Savings calculations
- Proposal PDF generation
- Admin dashboard
- Flutter mobile/web app

## Documentation

- **[workflow.md](workflow.md)** - Project milestones and timeline (10 milestones)
- **[django_backend_design.md](django_backend_design.md)** - Complete architecture, data models, API specs
- **[backend/README.md](backend/README.md)** - Backend-specific setup and commands

## Development

**Run tests:**
```bash
pytest
```

**Code formatting:**
```bash
black . && isort . && flake8
```

**Create migrations:**
```bash
python manage.py makemigrations
python manage.py migrate
```

## Example Usage

**Register:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "agent1",
    "email": "agent@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "role": "AGENT"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "agent1", "password": "SecurePass123!"}'
```

Returns JWT tokens for authenticated requests.

## Security Features

- JWT token authentication
- Role-based permissions (Admin/Agent)
- Password strength validation
- Secure password hashing
- CORS & CSRF protection
- IP address tracking
- MFA support (infrastructure ready)

## Contributing

See [django_backend_design.md](django_backend_design.md) for architecture details before contributing.

**Git workflow:**
1. Create feature branch: `git checkout -b feature/name`
2. Make changes and commit
3. Push and create pull request
