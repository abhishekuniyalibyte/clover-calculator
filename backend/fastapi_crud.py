"""
FastAPI CRUD API for Clover Payment Analysis Platform
Connects to the same PostgreSQL database used by Django.

Run with:
    pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv jinja2
    cd backend
    uvicorn fastapi_crud:app --reload --port 8001

Docs available at: http://127.0.0.1:8001/docs
Admin UI (for screenshots): http://127.0.0.1:8001/admin
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import declarative_base, Session, sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Database connection (reads from .env — same credentials as Django)
# ---------------------------------------------------------------------------

ENV_PATH = Path(__file__).resolve().parent / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

DB_NAME = os.getenv("DB_NAME", "clover_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

def _resolve_database_url() -> str:
    explicit = os.getenv("FASTAPI_DATABASE_URL") or os.getenv("DATABASE_URL")
    if explicit:
        return explicit

    django_settings_module = os.getenv("DJANGO_SETTINGS_MODULE", "")
    if django_settings_module.endswith("development"):
        sqlite_path = Path(__file__).resolve().parent / "db.sqlite3"
        return f"sqlite:///{sqlite_path.as_posix()}"

    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


DATABASE_URL = _resolve_database_url()

engine_kwargs: dict = {}
if DATABASE_URL.startswith("sqlite:"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------------------------------------------------------
# SQLAlchemy models (mirrors Django tables — no migration needed)
# ---------------------------------------------------------------------------

class UserORM(Base):
    __tablename__ = "accounts_user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), nullable=False)
    email = Column(String(254), default="")
    first_name = Column(String(150), default="")
    last_name = Column(String(150), default="")
    role = Column(String(10), default="AGENT")
    is_active = Column(Boolean, default=True)


class MerchantORM(Base):
    __tablename__ = "analyses_merchant"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"), nullable=False)
    business_name = Column(String(255), nullable=False)
    business_address = Column(Text, nullable=False, default="")
    contact_name = Column(String(255), default="")
    contact_email = Column(String(254), default="")
    contact_phone = Column(String(20), default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class AnalysisORM(Base):
    __tablename__ = "analyses_analysis"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"), nullable=False)
    merchant_id = Column(Integer, ForeignKey("analyses_merchant.id"), nullable=False)
    status = Column(String(20), default="DRAFT")
    current_processing_rate = Column(Numeric(5, 2), nullable=True)
    current_monthly_fees = Column(Numeric(10, 2), nullable=True)
    current_transaction_fees = Column(Numeric(10, 2), nullable=True)
    monthly_volume = Column(Numeric(12, 2), nullable=True)
    monthly_transaction_count = Column(Integer, nullable=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

# --- User (read-only) ---

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


# --- Merchant ---

class MerchantCreate(BaseModel):
    user_id: int
    business_name: str
    business_address: str = ""
    contact_name: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    notes: str = ""


class MerchantUpdate(BaseModel):
    business_name: Optional[str] = None
    business_address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    notes: Optional[str] = None


class MerchantResponse(BaseModel):
    id: int
    user_id: int
    business_name: str
    business_address: str
    contact_name: str
    contact_email: str
    contact_phone: str
    notes: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# --- Analysis ---

class AnalysisCreate(BaseModel):
    user_id: int
    merchant_id: int
    status: str = "DRAFT"
    current_processing_rate: Optional[float] = None
    current_monthly_fees: Optional[float] = None
    current_transaction_fees: Optional[float] = None
    monthly_volume: Optional[float] = None
    monthly_transaction_count: Optional[int] = None
    notes: str = ""


class AnalysisUpdate(BaseModel):
    status: Optional[str] = None
    current_processing_rate: Optional[float] = None
    current_monthly_fees: Optional[float] = None
    current_transaction_fees: Optional[float] = None
    monthly_volume: Optional[float] = None
    monthly_transaction_count: Optional[int] = None
    notes: Optional[str] = None


class AnalysisResponse(BaseModel):
    id: int
    user_id: int
    merchant_id: int
    status: str
    current_processing_rate: Optional[float]
    current_monthly_fees: Optional[float]
    current_transaction_fees: Optional[float]
    monthly_volume: Optional[float]
    monthly_transaction_count: Optional[int]
    notes: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# FastAPI app + dependency
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Clover CRUD API",
    description="FastAPI CRUD interface for the Clover Payment Analysis Platform database",
    version="1.0.0",
)

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


def get_db():
    db = SessionLocal()
    try:
        try:
            db.execute(text("SELECT 1"))
        except OperationalError:
            raise HTTPException(
                status_code=503,
                detail=f"Database unavailable. Check DATABASE_URL/DB_* settings. Current DATABASE_URL={DATABASE_URL}",
            )
        yield db
    finally:
        db.close()

def _admin_url(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return "/admin" + path


# ---------------------------------------------------------------------------
# Users endpoint (read-only — use this to find your user_id)
# ---------------------------------------------------------------------------

@app.get("/users/", response_model=list[UserResponse], tags=["Users"])
def list_users(db: Session = Depends(get_db)):
    return db.query(UserORM).filter(UserORM.is_active == True).all()

# ---------------------------------------------------------------------------
# Admin UI (simple HTML pages for screenshots/demo)
# ---------------------------------------------------------------------------

@app.get("/admin", include_in_schema=False)
def admin_home(request: Request, db: Session = Depends(get_db)):
    merchants_count = db.query(MerchantORM).count()
    analyses_count = db.query(AnalysisORM).count()
    users_count = db.query(UserORM).count()
    db_label = f"{DB_HOST}:{DB_PORT}/{DB_NAME} (user={DB_USER})"
    return templates.TemplateResponse(
        "fastapi_admin/home.html",
        {
            "request": request,
            "merchants_count": merchants_count,
            "analyses_count": analyses_count,
            "users_count": users_count,
            "db_label": db_label,
            "nav": {"home": _admin_url(""), "merchants": _admin_url("/merchants")},
        },
    )


@app.get("/admin/merchants", include_in_schema=False)
def admin_merchants(request: Request, message: str | None = None, db: Session = Depends(get_db)):
    users = (
        db.query(UserORM)
        .filter(UserORM.is_active == True)
        .order_by(UserORM.id.asc())
        .limit(200)
        .all()
    )
    merchants = db.query(MerchantORM).order_by(MerchantORM.id.desc()).limit(100).all()
    return templates.TemplateResponse(
        "fastapi_admin/merchants.html",
        {
            "request": request,
            "users": users,
            "merchants": merchants,
            "message": message,
            "nav": {"home": _admin_url(""), "merchants": _admin_url("/merchants")},
        },
    )


@app.get("/admin/merchants/{merchant_id}/edit", include_in_schema=False)
def admin_edit_merchant(request: Request, merchant_id: int, db: Session = Depends(get_db)):
    merchant = db.query(MerchantORM).filter(MerchantORM.id == merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    users = (
        db.query(UserORM)
        .filter(UserORM.is_active == True)
        .order_by(UserORM.id.asc())
        .limit(200)
        .all()
    )
    return templates.TemplateResponse(
        "fastapi_admin/merchant_edit.html",
        {
            "request": request,
            "merchant": merchant,
            "users": users,
            "nav": {"home": _admin_url(""), "merchants": _admin_url("/merchants")},
        },
    )


# ---------------------------------------------------------------------------
# Merchant endpoints
# ---------------------------------------------------------------------------

@app.post("/merchants/", response_model=MerchantResponse, status_code=201, tags=["Merchants"])
def create_merchant(data: MerchantCreate, db: Session = Depends(get_db)):
    user = db.query(UserORM).filter(UserORM.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=422, detail=f"Invalid user_id: {data.user_id} (user not found)")
    now = datetime.utcnow()
    merchant = MerchantORM(**data.model_dump(), created_at=now, updated_at=now)
    db.add(merchant)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=f"DB constraint error: {e.orig}")
    db.refresh(merchant)
    return merchant


@app.get("/merchants/", response_model=list[MerchantResponse], tags=["Merchants"])
def list_merchants(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(MerchantORM).offset(skip).limit(limit).all()


@app.get("/merchants/{merchant_id}", response_model=MerchantResponse, tags=["Merchants"])
def get_merchant(merchant_id: int, db: Session = Depends(get_db)):
    merchant = db.query(MerchantORM).filter(MerchantORM.id == merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return merchant


@app.patch("/merchants/{merchant_id}", response_model=MerchantResponse, tags=["Merchants"])
def update_merchant(merchant_id: int, data: MerchantUpdate, db: Session = Depends(get_db)):
    merchant = db.query(MerchantORM).filter(MerchantORM.id == merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(merchant, field, value)
    merchant.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(merchant)
    return merchant


@app.delete("/merchants/{merchant_id}", status_code=204, tags=["Merchants"])
def delete_merchant(merchant_id: int, db: Session = Depends(get_db)):
    merchant = db.query(MerchantORM).filter(MerchantORM.id == merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    db.delete(merchant)
    db.commit()


# ---------------------------------------------------------------------------
# Analysis endpoints
# ---------------------------------------------------------------------------

@app.post("/analyses/", response_model=AnalysisResponse, status_code=201, tags=["Analyses"])
def create_analysis(data: AnalysisCreate, db: Session = Depends(get_db)):
    user = db.query(UserORM).filter(UserORM.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=422, detail=f"Invalid user_id: {data.user_id} (user not found)")
    merchant = db.query(MerchantORM).filter(MerchantORM.id == data.merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=422, detail=f"Invalid merchant_id: {data.merchant_id} (merchant not found)")
    now = datetime.utcnow()
    analysis = AnalysisORM(**data.model_dump(), created_at=now, updated_at=now)
    db.add(analysis)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=f"DB constraint error: {e.orig}")
    db.refresh(analysis)
    return analysis


@app.get("/analyses/", response_model=list[AnalysisResponse], tags=["Analyses"])
def list_analyses(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(AnalysisORM).offset(skip).limit(limit).all()


@app.get("/analyses/{analysis_id}", response_model=AnalysisResponse, tags=["Analyses"])
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.query(AnalysisORM).filter(AnalysisORM.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@app.get("/merchants/{merchant_id}/analyses", response_model=list[AnalysisResponse], tags=["Analyses"])
def list_analyses_for_merchant(merchant_id: int, db: Session = Depends(get_db)):
    return db.query(AnalysisORM).filter(AnalysisORM.merchant_id == merchant_id).all()


@app.patch("/analyses/{analysis_id}", response_model=AnalysisResponse, tags=["Analyses"])
def update_analysis(analysis_id: int, data: AnalysisUpdate, db: Session = Depends(get_db)):
    analysis = db.query(AnalysisORM).filter(AnalysisORM.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(analysis, field, value)
    analysis.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(analysis)
    return analysis


@app.delete("/analyses/{analysis_id}", status_code=204, tags=["Analyses"])
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.query(AnalysisORM).filter(AnalysisORM.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    db.delete(analysis)
    db.commit()
