# Runbook: Platform Bootstrap

## 1. Prerequisites
- Google Cloud Project with Billing Enabled.
- `gcloud` CLI authenticated with administrative permissions.
- GitHub repository with Actions enabled.

---

## 2. Step-by-Step Bootstrap

### Step 1: Enable GCP Services
```bash
gcloud services enable \
  run.googleapis.com \
  firestore.googleapis.com \
  secretmanager.googleapis.com \
  iamcredentials.googleapis.com \
  aiplatform.googleapis.com \
  storage.googleapis.com \
  pubsub.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com
```

### Step 2: Initialize Terraform State Bucket & Firestore
```bash
# Create State Bucket with Object Versioning
gcloud storage buckets create gs://idp-poc-state-${PROJECT_ID} \
  --location=us-central1 \
  --uniform-bucket-level-access

gcloud storage buckets update gs://idp-poc-state-${PROJECT_ID} \
  --versioning

# Create Firestore Database in Native Mode
gcloud firestore databases create --location=nam5 --type=firestore-native
```

### Step 3: Populate Secret Manager
```bash
# Generate 32-byte JWT signing key
JWT_SECRET=$(openssl rand -hex 32)
echo -n "${JWT_SECRET}" | gcloud secrets create idp-jwt-signing-key --data-file=-

# Store fine-grained GitHub PAT
echo -n "${GITHUB_DISPATCH_PAT}" | gcloud secrets create idp-github-dispatch-token --data-file=-
```

### Step 4: Configure Workload Identity Federation (WIF)
```bash
# Create WIP Pool
gcloud iam workload-identity-pools create idp-pool \
  --location=global \
  --display-name="IDP Pipeline Pool"

# Create GitHub OIDC Provider
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=idp-pool \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref,attribute.environment=assertion.environment"
```

### Step 5: Seed Initial Platform Admin
```bash
python scripts/bootstrap_admin_user.py \
  --username admin_gov \
  --password "AdminPass123!" \
  --email "admin@idp.internal"
```
