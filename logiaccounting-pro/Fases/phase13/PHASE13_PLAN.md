# LogiAccounting Pro - Phase 13: Document Management System

## Enterprise Document Management with OCR & Digital Signatures

---

## 📋 EXECUTIVE SUMMARY

Phase 13 implements a comprehensive Document Management System (DMS) that transforms LogiAccounting Pro into a paperless enterprise platform. This system handles the complete document lifecycle from upload to archival, with intelligent OCR processing, version control, digital signatures, and AI-powered categorization.

### Business Value

| Benefit | Impact |
|---------|--------|
| **Paperless Operations** | 80% reduction in paper processing |
| **Time Savings** | Auto-extract data from invoices/receipts |
| **Compliance** | Audit trail for every document action |
| **Collaboration** | Share, comment, and approve documents |
| **Legal Validity** | Digital signatures with legal standing |
| **Search & Discovery** | Find any document in seconds |

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **File Storage** | Cloud storage with S3/Azure/GCS support |
| **OCR Engine** | Extract text from images and PDFs |
| **Smart Extraction** | AI-powered invoice/receipt data extraction |
| **Version Control** | Full history with diff comparison |
| **Digital Signatures** | eSignature with audit trail |
| **Templates** | Generate documents from templates |
| **Full-Text Search** | Search inside document content |
| **Auto-Categorization** | AI classifies documents automatically |

---

## 🏗️ ARCHITECTURE OVERVIEW

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DOCUMENT MANAGEMENT SYSTEM                            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Web Client    │     │  Mobile Client  │     │   API Client    │
│   (React)       │     │  (React Native) │     │   (External)    │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY                                      │
│                    (FastAPI + Upload Handler)                            │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Document       │     │   Processing    │     │    Search       │
│  Service        │     │   Pipeline      │     │    Engine       │
│                 │     │                 │     │                 │
│ - CRUD ops      │     │ - OCR Engine    │     │ - Elasticsearch │
│ - Versioning    │     │ - AI Extraction │     │ - Full-text     │
│ - Permissions   │     │ - Thumbnails    │     │ - Filters       │
│ - Sharing       │     │ - Virus Scan    │     │ - Facets        │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                       │
├─────────────────┬─────────────────┬─────────────────┬───────────────────┤
│   PostgreSQL    │   Object Store  │  Elasticsearch  │   Redis Cache     │
│   (Metadata)    │   (S3/Azure)    │   (Search)      │   (Sessions)      │
└─────────────────┴─────────────────┴─────────────────┴───────────────────┘

                    PROCESSING PIPELINE DETAIL
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐│
│  │ Upload   │──▶│  Virus   │──▶│   OCR    │──▶│    AI    │──▶│ Index  ││
│  │ Handler  │   │  Scan    │   │ Extract  │   │ Classify │   │ Search ││
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └────────┘│
│       │                             │               │                    │
│       ▼                             ▼               ▼                    │
│  ┌──────────┐                 ┌──────────┐   ┌──────────┐               │
│  │Thumbnail │                 │  Store   │   │  Link to │               │
│  │Generator │                 │ Metadata │   │ Entities │               │
│  └──────────┘                 └──────────┘   └──────────┘               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Document Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DOCUMENT LIFECYCLE                                  │
└─────────────────────────────────────────────────────────────────────────┘

    ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
    │ UPLOAD  │────▶│ PROCESS │────▶│  ACTIVE │────▶│ ARCHIVE │
    └─────────┘     └─────────┘     └─────────┘     └─────────┘
         │               │               │               │
         │               │               │               │
         ▼               ▼               ▼               ▼
    ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
    │ Validate│     │   OCR   │     │  Share  │     │  Retain │
    │ Scan    │     │ Extract │     │  Sign   │     │  Delete │
    │ Store   │     │ Classify│     │ Version │     │  Export │
    └─────────┘     └─────────┘     └─────────┘     └─────────┘

States:
  - UPLOADING: File being uploaded
  - PROCESSING: OCR/AI extraction in progress
  - PENDING_REVIEW: Requires human verification
  - ACTIVE: Available for use
  - SIGNED: Has valid signature(s)
  - ARCHIVED: Moved to cold storage
  - DELETED: Soft deleted (recoverable)
  - PURGED: Permanently removed
```

---

## 📁 PROJECT STRUCTURE

```
backend/app/
├── documents/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py           # Main document model
│   │   ├── document_version.py   # Version history
│   │   ├── document_category.py  # Categories/folders
│   │   ├── document_tag.py       # Tags for classification
│   │   ├── document_share.py     # Sharing permissions
│   │   ├── document_comment.py   # Comments/annotations
│   │   ├── signature.py          # Digital signatures
│   │   └── signature_request.py  # Signature workflows
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_service.py   # Main document operations
│   │   ├── storage_service.py    # S3/Azure/GCS abstraction
│   │   ├── ocr_service.py        # OCR processing
│   │   ├── extraction_service.py # AI data extraction
│   │   ├── search_service.py     # Elasticsearch operations
│   │   ├── signature_service.py  # Digital signature handling
│   │   ├── template_service.py   # Document generation
│   │   ├── thumbnail_service.py  # Preview generation
│   │   └── virus_scan_service.py # Malware detection
│   │
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── base_processor.py     # Base processor class
│   │   ├── pdf_processor.py      # PDF handling
│   │   ├── image_processor.py    # Image handling
│   │   ├── office_processor.py   # Word/Excel handling
│   │   └── invoice_processor.py  # Invoice-specific extraction
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── documents.py          # Document CRUD endpoints
│   │   ├── upload.py             # Upload endpoints
│   │   ├── search.py             # Search endpoints
│   │   ├── signatures.py         # Signature endpoints
│   │   ├── templates.py          # Template endpoints
│   │   └── categories.py         # Category endpoints
│   │
│   └── schemas/
│       ├── __init__.py
│       ├── document_schemas.py
│       ├── upload_schemas.py
│       ├── search_schemas.py
│       └── signature_schemas.py
│
├── workers/
│   ├── __init__.py
│   ├── celery_app.py             # Celery configuration
│   └── tasks/
│       ├── __init__.py
│       ├── ocr_tasks.py          # OCR processing tasks
│       ├── extraction_tasks.py   # AI extraction tasks
│       ├── thumbnail_tasks.py    # Thumbnail generation
│       ├── index_tasks.py        # Search indexing
│       └── cleanup_tasks.py      # Cleanup/archival tasks

frontend/src/
├── features/
│   └── documents/
│       ├── components/
│       │   ├── DocumentUploader.jsx
│       │   ├── DocumentViewer.jsx
│       │   ├── DocumentList.jsx
│       │   ├── DocumentCard.jsx
│       │   ├── DocumentPreview.jsx
│       │   ├── VersionHistory.jsx
│       │   ├── DocumentComments.jsx
│       │   ├── ShareDialog.jsx
│       │   ├── SignatureRequest.jsx
│       │   ├── SignaturePad.jsx
│       │   ├── CategoryTree.jsx
│       │   ├── TagSelector.jsx
│       │   ├── SearchFilters.jsx
│       │   └── BulkActions.jsx
│       │
│       ├── pages/
│       │   ├── DocumentsPage.jsx
│       │   ├── DocumentDetailPage.jsx
│       │   ├── SignatureRequestPage.jsx
│       │   └── TemplatesPage.jsx
│       │
│       ├── hooks/
│       │   ├── useDocuments.js
│       │   ├── useUpload.js
│       │   ├── useSearch.js
│       │   └── useSignature.js
│       │
│       └── services/
│           └── documentApi.js
│
└── components/
    └── common/
        ├── FileDropzone.jsx
        ├── PDFViewer.jsx
        └── ImageViewer.jsx
```

---

## 🔧 TECHNOLOGY STACK

### Backend Dependencies

```txt
# requirements.txt additions

# Storage
boto3==1.34.0                    # AWS S3
azure-storage-blob==12.19.0      # Azure Blob Storage
google-cloud-storage==2.14.0     # Google Cloud Storage

# OCR & Document Processing
pytesseract==0.3.10              # OCR engine
pdf2image==1.16.3                # PDF to image
PyPDF2==3.0.1                    # PDF manipulation
python-docx==1.1.0               # Word documents
openpyxl==3.1.2                  # Excel files
Pillow==10.2.0                   # Image processing
python-magic==0.4.27             # File type detection

# AI/ML for extraction
openai==1.12.0                   # GPT for smart extraction
anthropic==0.18.0                # Claude for extraction (alternative)
transformers==4.37.0             # Local models (optional)

# Search
elasticsearch==8.12.0            # Full-text search

# Background tasks
celery==5.3.6                    # Task queue
redis==5.0.1                     # Message broker

# Digital Signatures
cryptography==42.0.0             # Cryptographic operations
pyhanko==0.21.0                  # PDF signing

# Security
python-clamd==1.0.2              # ClamAV integration
```

### Frontend Dependencies

```json
{
  "dependencies": {
    "react-dropzone": "^14.2.3",
    "react-pdf": "^7.7.0",
    "@react-pdf-viewer/core": "^3.12.0",
    "signature_pad": "^4.1.7",
    "react-image-crop": "^11.0.1",
    "file-saver": "^2.0.5",
    "jszip": "^3.10.1"
  }
}
```

### Infrastructure

| Service | Provider Options |
|---------|------------------|
| **Object Storage** | AWS S3, Azure Blob, Google Cloud Storage, MinIO |
| **Search** | Elasticsearch, OpenSearch, Meilisearch |
| **OCR** | Tesseract, Google Vision, AWS Textract, Azure Form Recognizer |
| **Virus Scan** | ClamAV, VirusTotal API |
| **Task Queue** | Celery + Redis, AWS SQS |

---

## 📊 DATABASE SCHEMA

### Core Document Tables

```sql
-- Document Categories (Folders)
CREATE TABLE document_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    parent_id UUID REFERENCES document_categories(id),
    
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#3B82F6',
    icon VARCHAR(50) DEFAULT 'folder',
    
    -- Settings
    auto_categorize BOOLEAN DEFAULT FALSE,
    retention_days INTEGER,  -- NULL = forever
    
    -- Hierarchy
    path VARCHAR(1000),  -- Materialized path: /parent/child/grandchild
    level INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(organization_id, parent_id, slug)
);

-- Main Documents Table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    
    -- Basic Info
    name VARCHAR(500) NOT NULL,
    description TEXT,
    
    -- File Info
    original_filename VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL,
    file_hash VARCHAR(64) NOT NULL,  -- SHA-256
    
    -- Storage
    storage_provider VARCHAR(20) NOT NULL,  -- 's3', 'azure', 'gcs'
    storage_bucket VARCHAR(255) NOT NULL,
    storage_key VARCHAR(500) NOT NULL,
    storage_url TEXT,
    
    -- Thumbnails
    thumbnail_url TEXT,
    preview_url TEXT,
    
    -- Classification
    category_id UUID REFERENCES document_categories(id),
    document_type VARCHAR(50),  -- 'invoice', 'receipt', 'contract', 'report', etc.
    
    -- OCR & Extraction
    ocr_status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    ocr_text TEXT,
    ocr_confidence DECIMAL(5,2),
    extracted_data JSONB DEFAULT '{}',
    extraction_status VARCHAR(20) DEFAULT 'pending',
    
    -- AI Classification
    ai_category_suggestion VARCHAR(100),
    ai_confidence DECIMAL(5,2),
    ai_tags TEXT[],
    
    -- Relationships
    related_entity_type VARCHAR(50),  -- 'invoice', 'transaction', 'project', 'supplier', etc.
    related_entity_id UUID,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- 'uploading', 'processing', 'active', 'archived', 'deleted'
    
    -- Versioning
    current_version INTEGER DEFAULT 1,
    version_count INTEGER DEFAULT 1,
    
    -- Permissions
    visibility VARCHAR(20) DEFAULT 'private',  -- 'private', 'organization', 'public'
    owner_id UUID REFERENCES users(id),
    
    -- Signatures
    requires_signature BOOLEAN DEFAULT FALSE,
    signature_status VARCHAR(20),  -- 'pending', 'partial', 'completed'
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP,
    deleted_at TIMESTAMP,
    
    -- Search
    search_vector TSVECTOR,
    
    INDEX idx_documents_org (organization_id),
    INDEX idx_documents_category (category_id),
    INDEX idx_documents_status (status),
    INDEX idx_documents_type (document_type),
    INDEX idx_documents_entity (related_entity_type, related_entity_id),
    INDEX idx_documents_search USING GIN (search_vector)
);

-- Document Versions
CREATE TABLE document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    version_number INTEGER NOT NULL,
    
    -- File Info (snapshot)
    original_filename VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    
    -- Storage
    storage_key VARCHAR(500) NOT NULL,
    storage_url TEXT,
    
    -- Change Info
    change_summary TEXT,
    changed_by UUID REFERENCES users(id),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(document_id, version_number)
);

-- Document Tags
CREATE TABLE document_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    color VARCHAR(7) DEFAULT '#6B7280',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(organization_id, slug)
);

-- Document-Tag Junction
CREATE TABLE document_tag_assignments (
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES document_tags(id) ON DELETE CASCADE,
    
    assigned_by UUID REFERENCES users(id),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (document_id, tag_id)
);

-- Document Shares
CREATE TABLE document_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Share target (one of these)
    shared_with_user_id UUID REFERENCES users(id),
    shared_with_email VARCHAR(255),  -- External share
    
    -- Permissions
    permission VARCHAR(20) NOT NULL,  -- 'view', 'comment', 'edit', 'admin'
    can_download BOOLEAN DEFAULT TRUE,
    can_share BOOLEAN DEFAULT FALSE,
    
    -- Link sharing
    share_token VARCHAR(64) UNIQUE,
    is_link_share BOOLEAN DEFAULT FALSE,
    link_password_hash VARCHAR(255),
    
    -- Expiration
    expires_at TIMESTAMP,
    
    -- Metadata
    shared_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    
    INDEX idx_shares_document (document_id),
    INDEX idx_shares_user (shared_with_user_id),
    INDEX idx_shares_token (share_token)
);

-- Document Comments
CREATE TABLE document_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES document_comments(id),  -- For replies
    
    user_id UUID NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    
    -- Position (for annotations)
    page_number INTEGER,
    position_x DECIMAL(10,4),
    position_y DECIMAL(10,4),
    annotation_type VARCHAR(20),  -- 'highlight', 'note', 'drawing'
    annotation_data JSONB,
    
    -- Status
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_comments_document (document_id)
);

-- Digital Signatures
CREATE TABLE document_signatures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Signer
    signer_user_id UUID REFERENCES users(id),
    signer_email VARCHAR(255) NOT NULL,
    signer_name VARCHAR(255) NOT NULL,
    
    -- Signature Data
    signature_image TEXT,  -- Base64 or URL
    signature_type VARCHAR(20),  -- 'draw', 'type', 'upload', 'certificate'
    
    -- Certificate (for PKI signatures)
    certificate_serial VARCHAR(255),
    certificate_issuer VARCHAR(500),
    certificate_subject VARCHAR(500),
    
    -- Cryptographic proof
    signed_hash VARCHAR(128),
    signature_algorithm VARCHAR(50),
    
    -- Position
    page_number INTEGER,
    position_x DECIMAL(10,4),
    position_y DECIMAL(10,4),
    width DECIMAL(10,4),
    height DECIMAL(10,4),
    
    -- Audit
    ip_address INET,
    user_agent TEXT,
    geolocation JSONB,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'signed', 'declined', 'expired'
    signed_at TIMESTAMP,
    declined_at TIMESTAMP,
    decline_reason TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_signatures_document (document_id),
    INDEX idx_signatures_signer (signer_user_id)
);

-- Signature Requests (Workflows)
CREATE TABLE signature_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Request Info
    title VARCHAR(255),
    message TEXT,
    
    -- Workflow
    signing_order VARCHAR(20) DEFAULT 'any',  -- 'any', 'sequential'
    current_step INTEGER DEFAULT 1,
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft',  -- 'draft', 'sent', 'in_progress', 'completed', 'cancelled', 'expired'
    
    -- Requester
    requested_by UUID REFERENCES users(id),
    
    -- Deadlines
    due_date TIMESTAMP,
    reminder_frequency_days INTEGER DEFAULT 3,
    last_reminder_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP
);

-- Signature Request Signers
CREATE TABLE signature_request_signers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES signature_requests(id) ON DELETE CASCADE,
    
    -- Signer
    signer_email VARCHAR(255) NOT NULL,
    signer_name VARCHAR(255),
    
    -- Order (for sequential signing)
    signing_order INTEGER DEFAULT 1,
    
    -- Access
    access_token VARCHAR(64) UNIQUE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'viewed', 'signed', 'declined'
    viewed_at TIMESTAMP,
    signed_at TIMESTAMP,
    
    -- Link to actual signature
    signature_id UUID REFERENCES document_signatures(id),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document Templates
CREATE TABLE document_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    
    -- Template Type
    template_type VARCHAR(20) NOT NULL,  -- 'html', 'docx', 'pdf'
    
    -- Content
    content TEXT,  -- HTML/Handlebars template
    storage_key VARCHAR(500),  -- For file-based templates
    
    -- Variables
    variables JSONB DEFAULT '[]',  -- [{name, type, required, default}]
    
    -- Settings
    output_format VARCHAR(10) DEFAULT 'pdf',  -- 'pdf', 'docx', 'html'
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document Activity Log
CREATE TABLE document_activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    user_id UUID REFERENCES users(id),
    
    action VARCHAR(50) NOT NULL,
    -- 'created', 'viewed', 'downloaded', 'updated', 'versioned', 
    -- 'shared', 'unshared', 'commented', 'signed', 'archived', 'deleted'
    
    details JSONB DEFAULT '{}',
    
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_activity_document (document_id),
    INDEX idx_activity_created (created_at)
);
```

---

## 🔐 SECURITY SPECIFICATIONS

### Access Control

| Level | Description |
|-------|-------------|
| **Document Owner** | Full control |
| **Organization Admin** | All documents in org |
| **Explicit Share** | Based on share permissions |
| **Category Permission** | Inherited from category |
| **Public Link** | Token-based access |

### File Security

| Feature | Implementation |
|---------|----------------|
| **Virus Scanning** | ClamAV on upload |
| **File Validation** | Magic bytes + extension |
| **Encryption at Rest** | S3 SSE / Azure encryption |
| **Encryption in Transit** | TLS 1.3 |
| **Signed URLs** | Time-limited access |
| **Content Inspection** | Block executable content |

### Allowed File Types

```python
ALLOWED_MIME_TYPES = {
    # Documents
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain',
    'text/csv',
    
    # Images
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/tiff',
    'image/bmp',
    
    # Archives (for bulk upload)
    'application/zip',
}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_BULK_UPLOAD = 50  # files
```

---

## 🎯 FEATURE SPECIFICATIONS

### 13.1 File Upload & Storage

- **Chunked upload** for large files
- **Drag & drop** interface
- **Bulk upload** with progress tracking
- **Duplicate detection** via file hash
- **Auto-rename** for conflicts
- **Upload resume** on failure

### 13.2 OCR Processing

- **Automatic language detection**
- **Multi-page document support**
- **Handwriting recognition** (limited)
- **Table extraction**
- **Confidence scoring**
- **Manual correction interface**

### 13.3 AI Data Extraction

**Supported Document Types:**

| Type | Extracted Fields |
|------|-----------------|
| **Invoice** | Vendor, date, due date, line items, total, tax, currency |
| **Receipt** | Merchant, date, items, total, payment method |
| **Contract** | Parties, dates, terms, clauses |
| **Purchase Order** | PO number, items, quantities, delivery date |
| **Shipping Label** | Tracking, carrier, addresses, weight |

### 13.4 Version Control

- **Automatic versioning** on update
- **Version comparison** (diff)
- **Restore previous versions**
- **Version comments**
- **Major/minor versions**

### 13.5 Digital Signatures

- **Draw signature** on canvas
- **Type signature** with fonts
- **Upload signature** image
- **Sequential signing** workflows
- **Signature placement** on PDF
- **Email notifications**
- **Audit trail**

### 13.6 Full-Text Search

- **Content search** (OCR text)
- **Metadata search** (name, tags)
- **Filters** (type, date, category)
- **Faceted search**
- **Saved searches**
- **Recent searches**

---

## 🖥️ UI/UX SPECIFICATIONS

### Documents List View

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Documents                                           [+ Upload] [⚙]     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ 🔍 Search documents...                    [Type ▼] [Date ▼] [🔄]│    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌──────────────┐  ┌────────────────────────────────────────────────┐   │
│  │ 📁 All       │  │                                                │   │
│  │   Invoices   │  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐       │   │
│  │   Receipts   │  │  │ PDF  │  │ PDF  │  │ DOC  │  │ IMG  │       │   │
│  │   Contracts  │  │  │      │  │      │  │      │  │      │       │   │
│  │   Reports    │  │  └──────┘  └──────┘  └──────┘  └──────┘       │   │
│  │              │  │  Invoice   Invoice   Contract  Receipt        │   │
│  │ 🏷️ Tags     │  │  #001      #002      Draft     Oct-15         │   │
│  │   urgent     │  │  Oct 15    Oct 14    Oct 13    Oct 12         │   │
│  │   pending    │  │                                                │   │
│  │   approved   │  │  ─────────────────────────────────────────    │   │
│  │              │  │                                                │   │
│  │ ⏰ Recent    │  │  📄 Invoice_October_2024.pdf                   │   │
│  │              │  │     📁 Invoices • 2.4 MB • Oct 15, 2024       │   │
│  └──────────────┘  │     🏷️ urgent, pending-approval               │   │
│                    │     [View] [Download] [Share] [...]            │   │
│                    │                                                │   │
│                    │  📄 Contract_Supplier_ABC.docx                 │   │
│                    │     📁 Contracts • 1.1 MB • Oct 13, 2024      │   │
│                    │     ✍️ Pending signature (2/3)                 │   │
│                    │     [View] [Sign] [Share] [...]                │   │
│                    │                                                │   │
│                    └────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Document Viewer

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ← Back    Invoice_October_2024.pdf                    [⬇] [🔗] [✍️]    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────┐  ┌──────────────────┐  │
│  │                                             │  │ Details          │  │
│  │                                             │  ├──────────────────┤  │
│  │           ┌─────────────────────┐           │  │ Type: Invoice    │  │
│  │           │                     │           │  │ Size: 2.4 MB     │  │
│  │           │    INVOICE #001     │           │  │ Pages: 3         │  │
│  │           │                     │           │  │ Created: Oct 15  │  │
│  │           │    ABC Company      │           │  │ Owner: John D.   │  │
│  │           │                     │           │  │                  │  │
│  │           │    Amount: $5,432   │           │  │ ────────────────│  │
│  │           │    Due: Nov 15      │           │  │                  │  │
│  │           │                     │           │  │ 📊 Extracted     │  │
│  │           └─────────────────────┘           │  │ Vendor: ABC Co   │  │
│  │                                             │  │ Amount: $5,432   │  │
│  │           [◀ Page 1 of 3 ▶]                │  │ Due: Nov 15      │  │
│  │                                             │  │ [Link to Trans.] │  │
│  │                                             │  │                  │  │
│  └─────────────────────────────────────────────┘  │ ────────────────│  │
│                                                    │                  │  │
│  ┌─────────────────────────────────────────────┐  │ 📝 Comments (3)  │  │
│  │ 💬 Comments                          [+ Add]│  │                  │  │
│  ├─────────────────────────────────────────────┤  │ 📜 Versions (2)  │  │
│  │ John: Please review the amounts    10:30 AM │  │                  │  │
│  │ Sarah: Approved ✓                  11:45 AM │  │ 📤 Shares (1)    │  │
│  └─────────────────────────────────────────────┘  └──────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ⏱️ IMPLEMENTATION TIMELINE

| Week | Tasks | Hours |
|------|-------|-------|
| **Week 1** | Database schema, Storage service abstraction | 12h |
| **Week 2** | Upload system, File processing pipeline | 14h |
| **Week 3** | OCR integration, AI extraction | 16h |
| **Week 4** | Search indexing, Elasticsearch setup | 10h |
| **Week 5** | Version control, Document operations | 10h |
| **Week 6** | Digital signatures, Workflows | 14h |
| **Week 7** | Frontend: Upload, List, Viewer | 14h |
| **Week 8** | Frontend: Search, Comments, Share | 12h |
| **Week 9** | Templates, Generation | 8h |
| **Week 10** | Testing, Performance, Documentation | 10h |

**Total: ~120 hours (10 weeks)**

---

## ✅ FEATURE CHECKLIST

| # | Feature | Priority | Status |
|---|---------|----------|--------|
| 13.1 | Database schema & models | P0 | 🔲 |
| 13.2 | Storage service (S3/Azure/GCS) | P0 | 🔲 |
| 13.3 | File upload endpoint | P0 | 🔲 |
| 13.4 | Chunked upload support | P1 | 🔲 |
| 13.5 | File validation & virus scan | P0 | 🔲 |
| 13.6 | Thumbnail generation | P1 | 🔲 |
| 13.7 | OCR processing (Tesseract) | P0 | 🔲 |
| 13.8 | AI data extraction | P1 | 🔲 |
| 13.9 | Elasticsearch indexing | P0 | 🔲 |
| 13.10 | Full-text search API | P0 | 🔲 |
| 13.11 | Version control | P1 | 🔲 |
| 13.12 | Document sharing | P0 | 🔲 |
| 13.13 | Comments & annotations | P2 | 🔲 |
| 13.14 | Digital signatures | P1 | 🔲 |
| 13.15 | Signature workflows | P2 | 🔲 |
| 13.16 | Document templates | P2 | 🔲 |
| 13.17 | Categories & tags | P1 | 🔲 |
| 13.18 | Activity logging | P0 | 🔲 |
| 13.19 | Frontend: Upload UI | P0 | 🔲 |
| 13.20 | Frontend: Document list | P0 | 🔲 |
| 13.21 | Frontend: Document viewer | P0 | 🔲 |
| 13.22 | Frontend: Search UI | P0 | 🔲 |
| 13.23 | Frontend: Signature UI | P1 | 🔲 |
| 13.24 | Celery workers | P0 | 🔲 |

---

## 🔗 API ENDPOINTS

### Documents API

```
# Documents CRUD
GET    /api/v1/documents                    # List documents
POST   /api/v1/documents                    # Create document record
GET    /api/v1/documents/:id                # Get document
PUT    /api/v1/documents/:id                # Update document
DELETE /api/v1/documents/:id                # Delete document

# Upload
POST   /api/v1/documents/upload             # Upload file
POST   /api/v1/documents/upload/chunk       # Chunked upload
POST   /api/v1/documents/upload/complete    # Complete chunked upload
POST   /api/v1/documents/upload/bulk        # Bulk upload

# Download & Preview
GET    /api/v1/documents/:id/download       # Download file
GET    /api/v1/documents/:id/preview        # Get preview/thumbnail
GET    /api/v1/documents/:id/view           # Stream for viewer

# Versions
GET    /api/v1/documents/:id/versions       # List versions
POST   /api/v1/documents/:id/versions       # Create new version
GET    /api/v1/documents/:id/versions/:v    # Get specific version
POST   /api/v1/documents/:id/restore/:v     # Restore version

# Sharing
POST   /api/v1/documents/:id/share          # Share document
DELETE /api/v1/documents/:id/share/:sid     # Remove share
POST   /api/v1/documents/:id/share/link     # Create share link
GET    /api/v1/share/:token                 # Access shared document

# Comments
GET    /api/v1/documents/:id/comments       # List comments
POST   /api/v1/documents/:id/comments       # Add comment
PUT    /api/v1/documents/:id/comments/:cid  # Update comment
DELETE /api/v1/documents/:id/comments/:cid  # Delete comment

# Search
GET    /api/v1/documents/search             # Full-text search
POST   /api/v1/documents/search             # Advanced search

# Categories
GET    /api/v1/documents/categories         # List categories
POST   /api/v1/documents/categories         # Create category
PUT    /api/v1/documents/categories/:id     # Update category
DELETE /api/v1/documents/categories/:id     # Delete category

# Tags
GET    /api/v1/documents/tags               # List tags
POST   /api/v1/documents/tags               # Create tag
DELETE /api/v1/documents/tags/:id           # Delete tag

# Signatures
POST   /api/v1/documents/:id/signature/request  # Create signature request
GET    /api/v1/signature/requests/:id           # Get request status
POST   /api/v1/signature/sign/:token            # Sign document
POST   /api/v1/signature/decline/:token         # Decline signature

# Templates
GET    /api/v1/documents/templates          # List templates
POST   /api/v1/documents/templates          # Create template
POST   /api/v1/documents/templates/:id/generate  # Generate from template
```

---

*Phase 13 Plan - LogiAccounting Pro*
*Document Management System*
