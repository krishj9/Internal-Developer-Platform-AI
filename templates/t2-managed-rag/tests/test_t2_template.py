"""
Unit and integration tests for T2 Managed RAG template and scripts.
"""

import importlib.util
import sys
from pathlib import Path

import yaml


def _load_t2_module(module_name: str, rel_path: str):
    file_path = Path(__file__).parent.parent / rel_path
    dir_path = str(file_path.parent)
    if dir_path not in sys.path:
        sys.path.insert(0, dir_path)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


t2_client = _load_t2_module("t2_rag_client_mod", "scripts/rag_client.py")
t2_ingest = _load_t2_module("t2_ingest_mod", "scripts/ingest_documents.py")
t2_smoke = _load_t2_module("t2_smoke_mod", "scripts/smoke_test.py")


def test_t2_template_manifest_schema():
    """Verify template.yaml conforms to governed template schema."""
    manifest_path = Path(__file__).parent.parent / "template.yaml"
    assert manifest_path.exists(), "template.yaml must exist"

    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["id"] == "t2-managed-rag"
    assert data["version"] == "2.0.0"
    assert "dev" in data["supported_environments"]
    assert data["cost_tier"] == "medium"
    assert data["inputs"]["type"] == "object"
    assert data["inputs"]["additionalProperties"] is False

    # Check input constraints
    props = data["inputs"]["properties"]
    assert "corpus_name" in props
    assert "embedding_model" in props
    assert "chunk_size" in props
    assert "allowed_mime_types" in props

    # Check allowed outputs
    allowed_outputs = data["output_contract"]["allowed_outputs"]
    assert "deployment_id" in allowed_outputs
    assert "corpus_name" in allowed_outputs
    assert "corpus_resource_name" in allowed_outputs
    assert "embedding_model" in allowed_outputs
    assert "ingestion_status" in allowed_outputs


def test_t2_rag_client_retrieval():
    """Verify GovernedRagClient deterministic verification query."""
    client = t2_client.GovernedRagClient(
        corpus_name="test-corpus",
        embedding_model="text-embedding-004",
    )
    res = client.retrieve("What is the verification code for Managed RAG?")
    assert res["status"] == "success"
    assert res["corpus_name"] == "test-corpus"
    assert len(res["results"]) >= 1
    assert "IDP-RAG-VERIFIED-2026" in res["results"][0]["content"]


def test_t2_rag_client_empty_query():
    """Verify GovernedRagClient rejects empty query text."""
    client = t2_client.create_rag_client()
    res = client.retrieve("")
    assert res["status"] == "error"
    assert "Query text cannot be empty" in res["message"]


def test_t2_ingestion_manifest_validation():
    """Verify document validation limits MIME types, counts, and sizes."""
    # 1. Valid files
    valid_files = [
        {"uri": "gs://bucket/doc1.pdf", "mime_type": "application/pdf", "size_bytes": 1024 * 1024},
        {"uri": "gs://bucket/doc2.txt", "mime_type": "text/plain", "size_bytes": 2048},
    ]
    valid, msg = t2_ingest.validate_ingestion_manifest(valid_files)
    assert valid is True
    assert "valid" in msg.lower()

    # 2. Invalid URI prefix (non-GCS)
    invalid_uri = [
        {"uri": "https://example.com/doc.pdf", "mime_type": "application/pdf", "size_bytes": 100}
    ]
    valid, msg = t2_ingest.validate_ingestion_manifest(invalid_uri)
    assert valid is False
    assert "gs://" in msg

    # 3. Disallowed MIME type
    disallowed_mime = [
        {"uri": "gs://bucket/script.sh", "mime_type": "application/x-sh", "size_bytes": 100}
    ]
    valid, msg = t2_ingest.validate_ingestion_manifest(disallowed_mime)
    assert valid is False
    assert "MIME type" in msg

    # 4. Excessive file count
    excessive_files = [
        {"uri": f"gs://bucket/doc{i}.txt", "mime_type": "text/plain", "size_bytes": 10}
        for i in range(105)
    ]
    valid, msg = t2_ingest.validate_ingestion_manifest(excessive_files)
    assert valid is False
    assert "exceeds maximum limit" in msg


def test_t2_smoke_test_function():
    """Verify automated smoke test script returns True."""
    assert t2_smoke.run_smoke_test() is True
