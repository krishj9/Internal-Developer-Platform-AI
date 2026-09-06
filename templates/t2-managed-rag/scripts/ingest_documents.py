"""
Document ingestion validation and job execution for T2 Managed RAG.
"""

from typing import Any

APPROVED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/html",
    "text/markdown",
}

MAX_DOCUMENTS_LIMIT = 100
MAX_TOTAL_SIZE_MB = 500


def validate_ingestion_manifest(
    files: list[dict[str, Any]],
    allowed_mime_types: list[str] | None = None,
    max_count: int = 50,
    max_size_mb: int = 100,
) -> tuple[bool, str]:
    """
    Validate bounded document constraints before dispatching ingestion job.
    """
    if not files:
        return False, "Ingestion file list cannot be empty."

    if len(files) > max_count or len(files) > MAX_DOCUMENTS_LIMIT:
        max_allowed = min(max_count, MAX_DOCUMENTS_LIMIT)
        return False, f"File count ({len(files)}) exceeds maximum limit ({max_allowed})."

    effective_mimes = set(allowed_mime_types or APPROVED_MIME_TYPES)
    disallowed_configured = effective_mimes - APPROVED_MIME_TYPES
    if disallowed_configured:
        return False, f"Disallowed MIME types in configuration: {disallowed_configured}"

    total_bytes = 0
    for f in files:
        uri = f.get("uri", "")
        mime = f.get("mime_type", "")
        size = f.get("size_bytes", 0)

        if not uri.startswith("gs://"):
            return False, f"Invalid source URI '{uri}'. Must start with gs://"

        if mime not in effective_mimes:
            return False, f"MIME type '{mime}' is not permitted. Allowed: {effective_mimes}"

        total_bytes += size

    total_mb = total_bytes / (1024 * 1024)
    effective_max_mb = min(max_size_mb, MAX_TOTAL_SIZE_MB)
    if total_mb > effective_max_mb:
        return (
            False,
            (
                f"Total document size ({total_mb:.2f} MB) "
                f"exceeds allowed limit ({effective_max_mb} MB)."
            ),
        )

    return True, "Ingestion manifest is valid."
