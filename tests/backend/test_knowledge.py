import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.main import app
from backend.app.core.security import create_access_token
from backend.app.models.knowledge import Base, KnowledgeDocument, KnowledgeCategory, KnowledgeTag, AuditLog
from backend.app.services.document_service import KnowledgeDocumentService
from backend.app.services.validators import ValidationError
from tests.backend.test_auth import test_session

@pytest.fixture(scope="module", autouse=True)
async def setup_knowledge_tables():
    from tests.backend.test_auth import test_engine
    # Ensure user_domain and knowledge models are imported to register tables
    import backend.app.models.user_domain
    from backend.app.models.knowledge import (
        KnowledgeDocument,
        KnowledgeCategory,
        KnowledgeTag,
        AuditLog,
        KnowledgeVersion,
        KnowledgeAttachment
    )
    print("BEFORE CREATE_ALL metadata keys:", list(Base.metadata.tables.keys()))
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
        # Verify tables in the database file itself
        def get_db_tables(connection):
            import sqlite3
            cursor = connection.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            res = cursor.fetchall()
            return [r[0] for r in res]
        db_tables = await conn.run_sync(get_db_tables)
        print("AFTER CREATE_ALL database tables:", db_tables)
    
    # Register dependency override for knowledge test module
    from backend.app.core.dependencies import get_db_session
    from tests.backend.test_auth import override_get_db_session
    app.dependency_overrides[get_db_session] = override_get_db_session
    yield
    app.dependency_overrides.pop(get_db_session, None)
    await test_engine.dispose()

@pytest.mark.asyncio
async def test_knowledge_complete_flow():
    # 1. Access tokens
    admin_token = create_access_token("admin-1", ["Admin"])
    steward_token = create_access_token("steward-1", ["Steward"])
    
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    headers_steward = {"Authorization": f"Bearer {steward_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # --- Category CRUD ---
        res_cat = await ac.post("/api/v1/categories/", json={"name": "Emergency SOPs", "description": "SOPs for fire, crowd surge"}, headers=headers_admin)
        assert res_cat.status_code == 201
        cat_id = res_cat.json()["id"]

        # Put Category
        res_cat_put = await ac.put(f"/api/v1/categories/{cat_id}", json={"name": "Emergency SOPs Updated", "description": "Updated"}, headers=headers_admin)
        assert res_cat_put.status_code == 200
        assert res_cat_put.json()["name"] == "Emergency SOPs Updated"

        # List Categories
        res_cats_list = await ac.get("/api/v1/categories/", headers=headers_steward)
        assert res_cats_list.status_code == 200
        assert len(res_cats_list.json()) >= 1

        # --- Tag CRUD ---
        res_tag = await ac.post("/api/v1/tags/", json={"name": "CrowdControl"}, headers=headers_admin)
        assert res_tag.status_code == 201
        tag_id = res_tag.json()["id"]

        # Put Tag
        res_tag_put = await ac.put(f"/api/v1/tags/{tag_id}", json={"name": "CrowdControlUpdated"}, headers=headers_admin)
        assert res_tag_put.status_code == 200

        # List Tags
        res_tags_list = await ac.get("/api/v1/tags/", headers=headers_steward)
        assert res_tags_list.status_code == 200

        # --- Document Creation ---
        doc_payload = {
            "title": "Turnstile Ingress Guidelines",
            "content": "Step by step procedures for gate operations.",
            "metadata_json": {"priority": "medium"},
            "category_ids": [cat_id],
            "tag_ids": [tag_id]
        }
        res_doc = await ac.post("/api/v1/documents/", json=doc_payload, headers=headers_admin)
        assert res_doc.status_code == 201
        doc_data = res_doc.json()
        doc_id = doc_data["id"]
        assert doc_data["status"] == "DRAFT"
        assert len(doc_data["categories"]) == 1
        assert len(doc_data["tags"]) == 1

        # Duplicate title validation
        res_dup = await ac.post("/api/v1/documents/", json=doc_payload, headers=headers_admin)
        assert res_dup.status_code == 400

        # --- Document Update ---
        update_payload = {
            "title": "Turnstile Ingress Guidelines Updated",
            "content": "Step by step procedures for gate operations. (Updated)",
            "version_id": doc_data["version_id"],
            "metadata_json": {"priority": "high"}
        }
        res_update = await ac.put(f"/api/v1/documents/{doc_id}", json=update_payload, headers=headers_admin)
        assert res_update.status_code == 200
        updated_data = res_update.json()
        assert updated_data["version_id"] == 2

        # Optimistic Locking Conflict (409)
        res_conflict = await ac.put(f"/api/v1/documents/{doc_id}", json=update_payload, headers=headers_admin)
        assert res_conflict.status_code == 409

        # --- Category & Tag Assign / Remove ---
        # Assign tag
        res_assign_tag = await ac.post(f"/api/v1/documents/{doc_id}/tags", json={"tag_ids": [tag_id]}, headers=headers_admin)
        assert res_assign_tag.status_code == 200

        # Remove tag
        res_remove_tag = await ac.delete(f"/api/v1/documents/{doc_id}/tags/{tag_id}", headers=headers_admin)
        assert res_remove_tag.status_code == 200

        # Remove category
        res_remove_cat = await ac.delete(f"/api/v1/documents/{doc_id}/categories/{cat_id}", headers=headers_admin)
        assert res_remove_cat.status_code == 200

        # --- Attachments ---
        attach_payload = {
            "filename": "operations_sheet.xlsx",
            "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "checksum_sha256": "f" * 64,
            "content_length": 2048,
            "storage_provider": "minio",
            "storage_uri": "s3://bucket/operations_sheet.xlsx",
            "virus_scan_status": "clean"
        }
        res_attach = await ac.post(f"/api/v1/documents/{doc_id}/attachments", json=attach_payload, headers=headers_admin)
        assert res_attach.status_code == 200
        attach_id = res_attach.json()["attachment_id"]

        # Get attachment
        res_get_attach = await ac.get(f"/api/v1/documents/{doc_id}/attachments/{attach_id}", headers=headers_steward)
        assert res_get_attach.status_code == 200

        # --- Versions ---
        res_versions = await ac.get(f"/api/v1/documents/{doc_id}/versions", headers=headers_steward)
        assert res_versions.status_code == 200
        assert len(res_versions.json()) >= 1

        # --- Search & Pagination ---
        res_search = await ac.get(
            "/api/v1/documents/search",
            params={"title": "Turnstile", "limit": 5, "offset": 0},
            headers=headers_steward
        )
        assert res_search.status_code == 200
        assert "items" in res_search.json()
        assert "total" in res_search.json()

        # --- Document Lifecycle Service Operations & REST transitions ---
        # Note: DRAFT -> REVIEW -> APPROVED must happen to enable POST /publish
        async with test_session() as session:
            doc_srv = KnowledgeDocumentService(session)
            # Submit for Review
            await doc_srv.submit_for_review(doc_id, actor_id=1)
            # Approve
            await doc_srv.approve_document(doc_id, actor_id=1)

        # Publish document via API
        res_pub = await ac.post(f"/api/v1/documents/{doc_id}/publish", headers=headers_admin)
        assert res_pub.status_code == 200
        assert res_pub.json()["status"] == "PUBLISHED"

        # Archive document via API
        res_arc = await ac.post(f"/api/v1/documents/{doc_id}/archive", headers=headers_admin)
        assert res_arc.status_code == 200
        assert res_arc.json()["status"] == "ARCHIVED"

        # Restore document via API (ARCHIVED -> DRAFT)
        res_res = await ac.post(f"/api/v1/documents/{doc_id}/restore", headers=headers_admin)
        assert res_res.status_code == 200
        assert res_res.json()["status"] == "DRAFT"

        # Soft Delete via DELETE endpoint
        res_del = await ac.delete(f"/api/v1/documents/{doc_id}", headers=headers_admin)
        assert res_del.status_code == 200
        assert res_del.json()["status"] == "DELETED"

        # Cleanup categories and tags
        res_del_cat = await ac.delete(f"/api/v1/categories/{cat_id}", headers=headers_admin)
        assert res_del_cat.status_code == 204

        res_del_tag = await ac.delete(f"/api/v1/tags/{tag_id}", headers=headers_admin)
        assert res_del_tag.status_code == 204
