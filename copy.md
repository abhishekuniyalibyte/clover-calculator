# Clover Pricing Calculator – Backend Architecture

## Objective
Build a secure backend system that analyzes merchant card processing costs and generates Blockpay pricing proposals. The solution automates data extraction from statements, supports manual entry when needed, and maintains full security and auditability.

## Backend Requirements

### Core Features
- PDF upload with auto-extraction of merchant statement data (multiple processors)
- Support complex payment pricing models:
  - Cost-plus
  - iPlus
  - Discount rate
  - Flat
- Surcharge programs
- Dynamic cost comparison and savings calculations
- Admin-controlled configuration for pricing rules, devices, fees, and user permissions
- Role-based access control (admin vs agents)
- PDF proposal generation with branded summaries and disclaimers

### Fee Structure Support
- Qualified / non-qualified interchange
- Card brand and network fees
- Per-item transaction fees
- Monthly, one-time, and miscellaneous fees
- Internal device costs (Clover POS and Payment)

### Security Requirements
- Strong authentication with JWT tokens
- Encrypted data at rest and in transit
- Strict access boundaries between users
- Secure handling of uploaded PDFs and generated reports

## 1) Backend API Layer
The backend is the central system of record and control.

### Key Responsibilities
- Authentication and authorization (agent vs admin)
- Creation and lifecycle management of analyses
- Secure storage of uploaded statements and generated documents
- Pricing and savings calculations
- Submission workflows and notifications
- Audit logging and access control
- Admin-controlled configuration for pricing rules, devices, fees, and user permissions

### Infrastructure
- Secure cloud infrastructure (AWS)
- Encrypted data storage
- Strict access policies
- PostgreSQL database

## 2) Document Ingestion and Extraction
Automates the analysis of merchant statements.

### Flow
- Statements uploaded securely to cloud storage
- PDF text extraction using pdfplumber combined with LLaMA 4 Maverick via Groq API for intelligent data structuring
- Support multiple processors and statement layouts (Chase, Clover, Square, etc.)
- Key fields (rates, fees, volumes, transaction counts) normalized into standard schema
- Confidence scores assigned to extracted fields
- Low-confidence values flagged for review and correction
- Hybrid approach: text parsing with regex patterns, fallback to table extraction

### Fallback Support
If no statement is provided, system switches to manual-entry flow.

## 3) Pricing and Savings Engine
Deterministic calculation engine for consistent results.

### Inputs
- Merchant's current processing costs (extracted or manual)
- Blockpay proposed pricing
- Selected devices, accessories, and SaaS plans
- Pricing model and fee structure configuration

### Outputs
- Current processor total cost
- Blockpay proposed total cost
- Net and percentage savings
- Savings across multiple timeframes
- Structured data for charts and reporting

### Data Integrity
Each submission stores a complete pricing snapshot so historical results remain unchanged even if pricing tables are updated later.

## 4) PDF Generation
Backend generates branded proposal PDFs after submission.

### PDF Contents
- Competitor comparison
- Pricing breakdown
- Devices and SaaS details
- Savings charts and summaries
- Required disclaimers and compliance copy

Generated PDFs are stored securely and linked to the corresponding analysis.

## 5) Admin and Oversight
Admin layer provides visibility and control.

### Admin Capabilities
- View all analyses and submissions
- Track agent activity and submission history
- Revoke agent access when needed
- Review audit logs and basic reporting
- Configure pricing rules and fee structures
- Manage user permissions

## 6) Security and Compliance
Security is a core design principle for handling sensitive financial statements.

### Security Controls
- Encrypted data at rest and in transit
- Secure file uploads and downloads
- Role-based access control
- MFA support
- Immutable audit logs
- Configurable data retention policies
- JWT token authentication
- PBKDF2 password hashing

### Key Management
- **AWS KMS (Key Management Service)** - Centralized key management for encryption
- **Automatic key rotation** - Regular rotation of encryption keys
- **Separate keys per environment** - Development, staging, and production isolation
- **Audit trail for key access** - Complete logging of key usage

### Rate Limiting & Abuse Protection
- **API rate limiting** - Prevent excessive requests per user/IP
- **Request throttling** - Control concurrent operations
- **Upload size limits** - Restrict PDF file sizes
- **Request validation** - Input sanitization and validation
- **Monitoring and alerting** - Track suspicious patterns
- **IP-based restrictions** - Block malicious actors

## 7) Offline-First Sync Strategy
Enables agents to work without constant connectivity, particularly on iPad devices.

### Sync Architecture
- **Local-first data storage** - All data stored on device first
- **Background synchronization** - Automatic sync when connection available
- **Queue-based uploads** - Reliable upload retry mechanism
- **Optimistic updates** - Immediate UI feedback with eventual consistency

### Conflict Resolution
- **Last-write-wins strategy** - Timestamp-based conflict resolution
- **Server authority** - Server state takes precedence in conflicts
- **Conflict detection** - Version tracking on all mutable entities
- **User notification** - Alert users when conflicts are detected and resolved

### Multiple Draft Handling
- **Draft versioning** - Track multiple versions of incomplete analyses
- **Auto-save functionality** - Periodic local saves to prevent data loss
- **Draft synchronization** - Sync drafts across devices for same user
- **Abandoned draft cleanup** - Automatic cleanup of old, incomplete drafts

### Device-Level Encryption (iPad Storage)
- **iOS Keychain integration** - Secure credential storage
- **File-level encryption** - Encrypt all stored PDFs and sensitive data
- **Secure enclave usage** - Hardware-backed encryption for keys
- **Data wiping on logout** - Clear local data on user logout or device change

## 8) Cost Controls & Optimization
Managing operational costs, particularly for AI-powered extraction.

### AI Extraction Cost Management
- **Cost visibility dashboard** - Real-time tracking of AI API costs
- **Per-user cost tracking** - Monitor costs by agent and admin
- **Budget alerts** - Notifications when approaching cost thresholds
- **Usage analytics** - Detailed reports on extraction patterns

### Throttling & Batching
- **Request batching** - Group multiple extractions when possible
- **Rate limiting per user** - Prevent excessive AI API usage
- **Queue management** - Batch processing during off-peak hours
- **Cache extraction results** - Avoid re-processing identical documents
- **Fallback to manual entry** - Option to skip AI extraction for cost savings

### Resource Optimization
- **PDF preprocessing** - Optimize file sizes before extraction
- **Selective AI usage** - Use AI only for complex documents
- **Response caching** - Cache common extraction patterns
- **Cost allocation tracking** - Attribute costs to specific business units

## 9) Technology Stack

### Backend Framework & Core
- **Python 3.10+** - Primary programming language
- **Django 5.0.1** - Web framework
- **Django REST Framework 3.14.0** - RESTful API development
- **PostgreSQL** (psycopg2-binary 2.9.9) - Production database
- **SQLite** - Development database

### Authentication & Security
- **djangorestframework-simplejwt 5.3.1** - JWT token authentication
- **PBKDF2** - Password hashing algorithm
- **django-password-validators 1.7.1** - Password strength validation
- **django-cors-headers 4.3.1** - CORS handling
- **MFA Support** - Multi-factor authentication

### PDF Processing & Extraction
- **pdfplumber 0.11.0** - Fast PDF text extraction
- **PyMuPDF 1.23.26** - PDF rendering and manipulation
- **Pillow 10.2.0** - Image processing
- **groq 0.11.0** - LLaMA 4 Maverick integration via Groq API
- **Hybrid extraction approach** - Text parsing with regex patterns, fallback to table extraction

### Data Validation & Utilities
- **django-filter 23.5** - Advanced filtering for querysets
- **django-phonenumber-field 7.3.0** - Phone number validation
- **phonenumbers 8.13.27** - Phone number parsing library
- **pytz 2024.1** - Timezone support
- **python-decouple 3.8** - Environment variable management

### Frontend
- **React** - Modern JavaScript library for building user interfaces
- **Component-based architecture** - Reusable UI components

### Infrastructure & Cloud
- **AWS (Amazon Web Services)** - Cloud hosting platform
- **Encrypted Storage** - Data at rest encryption
- **Secure File Uploads** - S3 or equivalent for PDF storage

### Development Tools
- **Git** - Version control
- **pytest** - Testing framework (implied from Django best practices)
- **black** - Code formatting
- **isort** - Import sorting
- **flake8** - Code quality checking

### API & Integration
- **RESTful API** - JSON-based communication
- **Groq API** - LLM inference for intelligent data extraction
- **Factory Pattern** - Processor detection and routing

### Security Features
- JWT token-based authentication
- Role-based access control (RBAC)
- Encrypted data at rest and in transit
- File upload validation and sanitization
- Immutable audit logs
- Configurable data retention policies

## 10) Summary
This backend architecture provides extraction pipeline, pricing engine, and administrative controls to ensure scalability, security, and clarity. It supports automation where possible, manual input where required, and provides a consistent, auditable process for generating merchant pricing proposals and savings analyses.
