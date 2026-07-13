import json
from typing import Any

class ValidationError(Exception):
    def __init__(self, errors: dict[str, str]):
        super().__init__(str(errors))
        self.errors = errors


# Valid document statuses
VALID_STATUSES = {"DRAFT", "REVIEW", "APPROVED", "PUBLISHED", "ARCHIVED", "DELETED"}

# Document lifecycle transitions
# DRAFT -> REVIEW -> APPROVED -> PUBLISHED -> ARCHIVED -> DELETED
VALID_TRANSITIONS = {
    "DRAFT": {"REVIEW", "DELETED"},
    "REVIEW": {"DRAFT", "APPROVED", "DELETED"},
    "APPROVED": {"PUBLISHED", "DRAFT", "DELETED"},
    "PUBLISHED": {"ARCHIVED", "DELETED"},
    "ARCHIVED": {"PUBLISHED", "DRAFT", "DELETED"},
    "DELETED": {"DRAFT"} # Restoring document can put it back to DRAFT or its previous status
}

class KnowledgeValidator:
    @staticmethod
    def validate_document_create(
        title: str,
        content: str,
        metadata: dict[str, Any] | None,
        max_title_length: int = 255,
        max_metadata_size: int = 100 * 1024 # 100 KB
    ) -> None:
        errors = {}

        # Required fields
        if not title or not title.strip():
            errors["title"] = "Title is required"
        elif len(title) > max_title_length:
            errors["title"] = f"Title exceeds maximum length of {max_title_length} characters"

        if not content or not content.strip():
            errors["content"] = "Content is required"

        # Metadata size and schema verification
        if metadata is not None:
            if not isinstance(metadata, dict):
                errors["metadata"] = "Metadata must be a key-value dictionary"
            else:
                try:
                    serialized_meta = json.dumps(metadata)
                    if len(serialized_meta.encode("utf-8")) > max_metadata_size:
                        errors["metadata"] = f"Metadata size exceeds maximum limit of {max_metadata_size} bytes"
                except (TypeError, ValueError):
                    errors["metadata"] = "Metadata is not JSON serializable"

        if errors:
            raise ValidationError(errors)

    @staticmethod
    def validate_status_transition(current_status: str, target_status: str) -> None:
        if current_status not in VALID_STATUSES:
            raise ValidationError({"status": f"Invalid current status: {current_status}"})
        if target_status not in VALID_STATUSES:
            raise ValidationError({"status": f"Invalid target status: {target_status}"})
        
        if current_status == target_status:
            return # No-op transitions are allowed
            
        allowed_targets = VALID_TRANSITIONS.get(current_status, set())
        if target_status not in allowed_targets:
            raise ValidationError({
                "status": f"Invalid status transition from {current_status} to {target_status}"
            })

    @staticmethod
    def validate_attachment_metadata(
        filename: str,
        mime_type: str,
        checksum_sha256: str,
        content_length: int,
        storage_provider: str,
        storage_uri: str,
        virus_scan_status: str,
        max_attachment_metadata_size: int = 50 * 1024 # 50 KB
    ) -> None:
        errors = {}

        if not filename or not filename.strip():
            errors["filename"] = "Filename is required"
        if not mime_type or not mime_type.strip():
            errors["mime_type"] = "MIME type is required"
        if not checksum_sha256 or not checksum_sha256.strip():
            errors["checksum_sha256"] = "Checksum SHA-256 is required"
        elif len(checksum_sha256) != 64:
            errors["checksum_sha256"] = "Checksum SHA-256 must be exactly 64 characters long"
        
        if content_length <= 0:
            errors["content_length"] = "Content length must be greater than zero"
        
        if not storage_provider or not storage_provider.strip():
            errors["storage_provider"] = "Storage provider is required"
        if not storage_uri or not storage_uri.strip():
            errors["storage_uri"] = "Storage URI is required"
            
        if not virus_scan_status or not virus_scan_status.strip():
            errors["virus_scan_status"] = "Virus scan status is required"
        elif virus_scan_status not in {"clean", "infected", "pending"}:
            errors["virus_scan_status"] = "Virus scan status must be clean, infected, or pending"

        # Validate total metadata size
        metadata_payload = {
            "filename": filename,
            "mime_type": mime_type,
            "checksum_sha256": checksum_sha256,
            "content_length": content_length,
            "storage_provider": storage_provider,
            "storage_uri": storage_uri,
            "virus_scan_status": virus_scan_status
        }
        try:
            serialized_meta = json.dumps(metadata_payload)
            if len(serialized_meta.encode("utf-8")) > max_attachment_metadata_size:
                errors["attachment_metadata"] = f"Attachment metadata size exceeds limit of {max_attachment_metadata_size} bytes"
        except Exception:
            errors["attachment_metadata"] = "Attachment metadata is not JSON serializable"

        if errors:
            raise ValidationError(errors)

    @staticmethod
    def validate_version_sequence(latest_version: int, next_version: int) -> None:
        if next_version != latest_version + 1:
            raise ValidationError({
                "version_sequence": f"Invalid version sequence. Next version must be {latest_version + 1}, got {next_version}"
            })
