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

## PDF Extraction

The system uses a hybrid approach for extracting data from merchant statements:

### Tools Used
- **pdfplumber** - PDF text extraction (fast, handles most PDFs)
- **LLaMA 4 Maverick via Groq API** - Intelligent data extraction and structuring
- **PyMuPDF** - PDF rendering

### Installation

All dependencies are Python packages installed via pip. No system dependencies required.

```bash
pip install -r requirements/base.txt
```

Add GROQ_API_KEY to your .env file:
```bash
GROQ_API_KEY=your_groq_api_key_here
```

### How It Works

1. Upload PDF via dashboard or API
2. System extracts text using pdfplumber
3. LLaMA 4 Maverick intelligently parses and structures the extracted data
4. Processor-specific extractors identify data patterns (Chase, Clover, etc.)
5. Data is saved to database with confidence score

### Supported Processors

- ✅ **Chase Paymentech** - Fully implemented
- ⏳ **Clover** - Planned
- ⏳ **Square** - Planned
- ⏳ **Stripe** - Planned

### Extraction Confidence

- **80-100%** - High confidence, minimal review needed
- **50-79%** - Partial extraction, requires review
- **< 50%** - Failed extraction, manual entry recommended

### Testing Extraction

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/statements/upload/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@statement.pdf"

# Via Dashboard
# Open http://localhost:8000/dashboard.html
# Upload PDF and view extracted data
```

## Documentation

- **[Main README](../README.md)** - Project overview & quick start
- **[Architecture Doc](../django_backend_design.md)** - Complete system design
- **[Workflow](../workflow.md)** - Project milestones
- **[Extraction Docs](apps/statements/extractors/README.md)** - PDF extraction details
