# Project Milestones and Estimated Effort

## Client-Provided Requirements (PDF FinTech Statement Work)

### Core requirements
- iPad-first and web-compatible application (responsive, touch-optimized)
- Offline mode with draft saving and secure data sync when online
- PDF upload with auto-extraction of merchant statement data (multiple processors)
- Support for complex payment pricing models (to be explained by client), including:
  - Cost-plus
  - iPlus
  - Discount rate
  - Flat
- Surcharge programs
- Dynamic cost comparison and savings calculations
- Visual charts and graphs showing savings across multiple timeframes:
  - Daily, weekly, monthly, quarterly, yearly
- Admin-controlled configuration for pricing rules, devices, fees, and user permissions
- Secure role-based access control (admin vs agents)
- Client-ready PDF output with branded summaries and required disclaimers

### Fully customizable fee structures
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

### Client milestone target (as shared)
- **Discovery + System Architecture** by **3rd Feb** (year not specified)

## Milestone 1: Discovery and Final Requirements
- **Duration:** 15–20 hours
- **Scope:**
  - Review Clover pricing datasets and agent journey
  - Finalize calculation logic (fixed vs flexible rates, fees, savings timelines)
  - Confirm supported pricing models (Cost-plus, iPlus, Discount rate, Flat) and surcharge program rules
  - Define input fields for statement-based and manual-entry flows
  - Confirm PDF structure and branding expectations
- **Deliverable:**
  - Finalized functional and calculation requirements
  - Approved scope baseline

## Milestone 2: System Architecture and Data Design
- **Duration:** 12–15 hours
- **Scope:**
  - Define overall system architecture (app, backend, extraction, storage)
  - Design data models for analyses, pricing snapshots, audit logs
  - Define security model (roles, access control, retention)
  - Define admin-configurable catalogs (pricing rules, devices, fees, user permissions)
- **Deliverable:**
  - Architecture document and data model sign-off

## Milestone 3: Flutter App – Core Agent Workflow
- **Duration:** 45–55 hours
- **Scope:**
  - Agent authentication and session handling
  - Create analysis and merchant profile screens
  - Statement upload (PDF/image)
  - Manual-entry fallback flow
  - Device and SaaS selection UI
  - Draft saving and offline support
  - Responsive, touch-optimized UI (iPad-first; web compatible)
- **Deliverable:**
  - Functional agent app covering end-to-end workflow (without automation)

## Milestone 4: Document Extraction and Normalization
- **Duration:** 35–45 hours
- **Scope:**
  - Secure statement upload to cloud storage
  - PDF and image extraction pipeline
  - Support multiple statement formats/processors
  - Normalize rates, fees, volumes, and counts
  - Confidence scoring and review flags
- **Deliverable:**
  - Automated extraction service integrated with the app

## Milestone 5: Pricing and Savings Engine
- **Duration:** 25–30 hours
- **Scope:**
  - Competitor cost calculation logic
  - Blockpay proposal calculation logic
  - Savings computation across multiple timeframes
  - Pricing snapshot versioning for historical accuracy
- **Deliverable:**
  - Verified calculation engine with test scenarios

## Milestone 6: Charts and Results Visualization
- **Duration:** 12–15 hours
- **Scope:**
  - Savings comparison views
  - Timeframe-based charts (daily, weekly, monthly, quarterly, yearly)
  - Clear breakdown of current vs proposed costs
- **Deliverable:**
  - Final results and visualization screens

## Milestone 7: PDF Proposal Generation
- **Duration:** 15–20 hours
- **Scope:**
  - Branded PDF template
  - Populate pricing, devices, SaaS, and charts
  - Add required disclaimers and compliance copy
  - Secure storage and download links
- **Deliverable:**
  - Client-ready proposal PDF generation

## Milestone 8: Admin Controls and Auditability
- **Duration:** 15–18 hours
- **Scope:**
  - Admin role access
  - View submissions and agent activity
  - Access revocation
  - Audit logs and basic reporting
- **Deliverable:**
  - Admin oversight functionality

## Milestone 9: Security Hardening and Deployment
- **Duration:** 12–15 hours
- **Scope:**
  - Encryption, IAM policies, secure file handling (PDF uploads and generated reports)
  - MFA support (if applicable)
  - Environment setup (dev / staging / prod)
  - Logging and monitoring
- **Deliverable:**
  - Production-ready deployment

## Milestone 10: QA, UAT, and Handoff
- **Duration:** 18–22 hours
- **Scope:**
  - End-to-end testing
  - Edge cases (partial statements, missing data)
  - Bug fixes and polish
  - Knowledge transfer and documentation
- **Deliverable:**
  - Production release approval

## Estimated Total Effort
- **Total:** ~200–240 hours
