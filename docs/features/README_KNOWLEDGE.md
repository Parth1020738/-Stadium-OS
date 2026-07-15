# Knowledge Service

The Knowledge Service provides access to standard operating procedures (SOPs), stadium guidelines, and tournament operations reference material.

## Architecture

This service conforms to **Clean Architecture** principles. Dependencies flow inward:

```
┌─────────────────────────────────────────────────────────────┐
│ Interface Adapters: HTTP Controllers (FastAPI)              │
│   v                                                         │
│   ┌───────────────────────────────────────────────────────┐ │
│   │ Use Cases: Services Layer (Business Logic)            │ │
│   │   v                                                   │ │
│   │   ┌─────────────────────────────────────────────────┐ │ │
│   │   │ Entities / Domain Models: (SQLAlchemy Models)    │ │ │
│   │   └─────────────────────────────────────────────────┘ │ │
│   └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Entity-Relationship (ER) Diagram

The relations of the Knowledge schema are modeled below:

```mermaid
erDiagram
    KnowledgeDocument {
        int id PK
        string title
        string content
        string status
        int owner_id FK
        datetime created_at
        datetime updated_at
        datetime published_at
        datetime archived_at
        boolean is_deleted
        int version_number
        int version_id
        json metadata
    }
    KnowledgeCategory {
        int id PK
        string name
        string description
    }
    KnowledgeTag {
        int id PK
        string name
    }
    KnowledgeVersion {
        int id PK
        int document_id FK
        int version_number
        string title
        string content
        json metadata
        datetime created_at
        int created_by FK
    }
    KnowledgeAttachment {
        string attachment_id PK
        int document_id FK
        string filename
        string mime_type
        string checksum_sha256
        int content_length
        string storage_provider
        string storage_uri
        string virus_scan_status
        int uploaded_by FK
        datetime uploaded_at
    }
    AuditLog {
        int id PK
        string action
        int document_id
        int user_id FK
        json details
        datetime timestamp
    }

    KnowledgeDocument }|--|{ KnowledgeCategory : "document_categories"
    KnowledgeDocument }|--|{ KnowledgeTag : "document_tags"
    KnowledgeDocument ||--o{ KnowledgeVersion : "has versions"
    KnowledgeDocument ||--o{ KnowledgeAttachment : "has attachments"
```

---

## Sequence Diagram: Creating and Publishing a Document

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Command Center Operator
    participant API as FastAPI Router
    participant Service as KnowledgeDocumentService
    participant Repo as KnowledgeDocumentRepository
    participant DB as SQLite / PostgreSQL

    Admin->>API: POST /api/v1/documents (Title, Content, Category/Tag IDs)
    Note over API: JWT validation and Role check
    API->>Service: create_document()
    Note over Service: Validate title length & metadata size
    Service->>Repo: get_by_title()
    Repo-->>Service: None (Unique Check OK)
    Service->>Repo: create(document)
    Repo->>DB: INSERT into knowledge_documents
    Service->>Repo: create(initial_ver)
    Repo->>DB: INSERT into knowledge_versions
    Service->>Repo: create(audit_log)
    Repo->>DB: INSERT into audit_log
    Service-->>API: Document Entity
    API-->>Admin: KnowledgeDocumentOut DTO

    Note over Admin, DB: Request Approval flow transitions status to APPROVED
    
    Admin->>API: POST /api/v1/documents/{id}/publish
    API->>Service: publish_document()
    Note over Service: Validate status transition APPROVED ➔ PUBLISHED
    Service->>Repo: save(document)
    Repo->>DB: UPDATE status, published_at
    Service-->>API: Document Entity
    API-->>Admin: KnowledgeDocumentOut DTO
```

---

## Environment Variables

Specify the following backend configurations in `.env`:

```ini
# Database Connection String
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aegis_db?sslmode=disable

# JWT Secret
JWT_SECRET=super-secure-jwt-secret-key-32-chars-long
```

---

## OpenAPI Usage Guide

FastAPI automatically generates the OpenAPI schema and documents the endpoints.
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

All endpoints require JWT authorization passed via header:
`Authorization: Bearer <JWT_TOKEN>`

### Examples: Searching Documents
Query filters are translated directly to SQL select operations:
`GET /api/v1/documents/search?title=Surge&status=PUBLISHED&limit=10&offset=0`

---

## Database Migration Guide

If deploying to PostgreSQL in staging or production environments, run Alembic migrations:
```powershell
alembic revision --autogenerate -m "Add knowledge models"
alembic upgrade head
```

---

## Testing Strategy

The test suite runs by default against an in-memory SQLite database (`sqlite+aiosqlite`) for fast, local development. 
To run integration tests against a PostgreSQL instance, set the `TEST_DATABASE_URL` environment variable:
```powershell
$env:TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/aegis_test_db"
pytest tests/
```

The CI/CD pipeline runs the complete Python unit and integration testing suite against both SQLite and a real PostgreSQL container service.

---

## Architectural Decision: Category & Tag Lifecycle

Categories and Tags utilize **hard delete** operations rather than soft delete:
1. **Low Data Complexity**: Unlike document resources, categories and tags represent basic vocabulary terms without complicated historical versioning.
2. **Referential Integrity**: Many-to-many relationship association tables (`document_categories`, `document_tags`) cascade deletes cleanly, ensuring no database-level orphans or broken constraints.
3. **API Simplicity**: Prevents breaking changes and maintains a clean, low-overhead REST interface layout.

