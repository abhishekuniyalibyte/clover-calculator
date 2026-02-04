# Clover Pricing Calculator – Architecture Overview

## Objective
The goal of this system is to build a secure, sales-agent–focused calculator application that analyzes a merchant’s card processing costs and generates a Blockpay pricing proposal with clear, defensible savings. The solution is designed to reduce manual work, support both automated and manual data entry, and maintain full control, security, and auditability.

## Client-Provided Requirements (PDF FinTech Statement Work)

### Product requirements
- iPad-first and web-compatible application (responsive, touch-optimized)
- Offline mode with draft saving and secure data sync when online
- PDF upload with auto-extraction of merchant statement data (multiple processors)
- Support complex payment pricing models, including:
  - Cost-plus
  - iPlus
  - Discount rate
  - Flat
- Surcharge programs
- Dynamic cost comparison and savings calculations
- Visual charts/graphs showing savings across multiple timeframes (daily, weekly, monthly, quarterly, yearly)
- Admin-controlled configuration for pricing rules, devices, fees, and user permissions
- Secure role-based access control (admin vs agents)
- Client-ready PDF output with branded summaries and required disclaimers

### Fee structure requirements
- Qualified / non-qualified interchange
- Card brand and network fees
- Per-item transaction fees
- Monthly, one-time, and miscellaneous fees
- Internal device costs (Clover POS and Payment)

### Security requirements
- Secure authentication (strong auth, MFA if applicable)
- Encrypted data at rest and in transit
- Strict access boundaries between users
- Secure handling of uploaded PDFs and generated reports

## 1) Client Application (Flutter)
The client-facing application is built using Flutter and used by internal sales agents.

### Key responsibilities
- Secure login with role-based access
- iPad-first UX and web compatibility (responsive, touch-optimized)
- Create and manage merchant analyses
- Upload processing statements (PDF or image)
- Support full manual data entry when statements are unavailable
- Review and correct extracted pricing and fee data
- Select devices, accessories, and SaaS plans from a controlled pricing catalog
- Configure Blockpay proposal pricing (fixed and flexible components)
- View savings results and comparison charts
- Submit analyses and generate proposal PDFs

The app supports offline drafts, with secure synchronization once connectivity is available.

## 2) Backend API Layer
The backend acts as the central system of record and control.

### Key responsibilities
- Authentication and authorization (agent vs admin)
- Creation and lifecycle management of analyses
- Secure storage of uploaded statements and generated documents
- Pricing and savings calculations
- Submission workflows and notifications
- Audit logging and access control
- Admin-controlled configuration for pricing rules, devices, fees, and user permissions

The backend is designed to run on a secure cloud infrastructure (AWS), with encrypted data storage and strict access policies.

## 3) Document Ingestion and Extraction
This layer automates the analysis of merchant statements.

### Flow
- Statements are uploaded securely to cloud storage
- PDF text extraction or OCR is applied, depending on document type
- Support multiple processors and statement layouts (template-based + ML/OCR fallback)
- Key fields (rates, fees, volumes, transaction counts) are normalized into a standard schema
- Confidence scores are assigned to extracted fields
- Low-confidence values are flagged for agent review and correction

If no statement is provided, the system switches seamlessly to a guided manual-entry flow.

## 4) Pricing and Savings Engine
A deterministic calculation engine ensures consistent and transparent results.

### Inputs
- Merchant’s current processing costs (extracted or manual)
- Blockpay proposed pricing
- Selected devices, accessories, and SaaS plans
- Pricing model and fee structure configuration (admin-controlled)

### Outputs
- Current processor total cost
- Blockpay proposed total cost
- Net and percentage savings
- Savings across multiple timeframes
- Structured data for charts and reporting

Each submission stores a complete pricing snapshot so historical results remain unchanged even if pricing tables are updated later.

## 5) PDF Generation
After submission, the backend generates a branded proposal PDF.

### The PDF includes
- Competitor comparison
- Pricing breakdown
- Devices and SaaS details
- Savings charts and summaries
- Required disclaimers and compliance copy (client-ready output)

Generated PDFs are stored securely and linked to the corresponding analysis.

## 6) Admin and Oversight
An admin layer provides visibility and control.

### Admin capabilities
- View all analyses and submissions
- Track agent activity and submission history
- Revoke agent access when needed
- Review audit logs and basic reporting

## 7) Security and Compliance
Because the system handles sensitive financial statements, security is a core design principle.

### Controls include
- Encrypted data at rest and in transit
- Secure file uploads and downloads
- Role-based access control
- MFA support (if applicable)
- Immutable audit logs
- Configurable data retention policies

## Summary
This architecture separates the client app, extraction pipeline, pricing engine, and administrative controls to ensure scalability, security, and clarity. It supports automation where possible, manual input where required, and provides a consistent, auditable process for generating merchant pricing proposals and savings analyses.
