# T2 Managed RAG Template

Governed Vertex AI RAG Engine stack with RagManagedDb and bounded GCS document ingestion.

## Capabilities

- Vertex AI RAG Engine with RagManagedDb vector index.
- Dedicated runtime service account (`sa-t2-...`) scoped with `roles/aiplatform.user`, `roles/storage.objectViewer`, and `roles/logging.logWriter`.
- Bounded document ingestion schema: validates MIME types (`application/pdf`, `text/plain`, `text/html`, `text/markdown`), maximum document count ($\le 100$), and maximum cumulative size ($\le 500$ MB).
- Automated readiness validation via deterministic retrieval from known smoke document.

## Explicitly Deferred

- Vertex AI Search backend.
- Self-managed pgvector, Cloud SQL, AlloyDB.
- Unbounded document uploads or arbitrary connectors.

## Lifecycle Operations

- **Create**: Provisions dedicated service account, IAM bindings, initializes corpus, ingests bounded documents, and executes readiness test.
- **Readiness**: Smoke test retrieves known verification code (`IDP-RAG-VERIFIED-2026`).
- **Destroy**: Deletes Vertex AI RAG Corpus, vector index, runtime service account, and IAM bindings.
