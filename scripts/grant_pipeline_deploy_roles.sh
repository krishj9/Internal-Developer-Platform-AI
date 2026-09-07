#!/usr/bin/env bash
# ==============================================================================
# Grant Pipeline Service Account Permissions for Cloud Run & Firebase Deployment
# ==============================================================================
# This script grants the required GCP IAM roles to the pipeline service account
# (idp-pipeline-t1-dev) so GitHub Actions can build and deploy the API to
# Cloud Run and the Portal to Firebase Hosting using keyless WIF authentication.
#
# Usage:
#   bash scripts/grant_pipeline_deploy_roles.sh [PROJECT_ID] [PIPELINE_SA_EMAIL] [RUNTIME_SA_EMAIL]
# ==============================================================================

set -euo pipefail

PROJECT_ID="${1:-${GCP_PROJECT:-mybrightday-dev}}"
PIPELINE_SA="${2:-idp-pipeline-t1-dev@${PROJECT_ID}.iam.gserviceaccount.com}"
RUNTIME_SA="${3:-idp-api-runtime@${PROJECT_ID}.iam.gserviceaccount.com}"

echo "================================================================="
echo "🔑 Granting Deployment IAM Roles for GitHub Actions Pipeline"
echo "================================================================="
echo "  • GCP Project:        ${PROJECT_ID}"
echo "  • Pipeline Identity:  ${PIPELINE_SA}"
echo "  • API Runtime SA:     ${RUNTIME_SA}"
echo "================================================================="
echo ""

# 1. Cloud Run Deployment Roles
echo "1. Granting Cloud Run Admin (roles/run.admin)..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${PIPELINE_SA}" \
  --role="roles/run.admin" \
  --condition=None --quiet

# 2. Service Account User on Runtime Identity
echo "2. Granting Service Account User on API Runtime SA..."
gcloud iam service-accounts add-iam-policy-binding "${RUNTIME_SA}" \
  --project="${PROJECT_ID}" \
  --member="serviceAccount:${PIPELINE_SA}" \
  --role="roles/iam.serviceAccountUser" \
  --condition=None --quiet

# 3. Cloud Build & Container Staging Roles
echo "3. Granting Cloud Build Editor (roles/cloudbuild.builds.editor)..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${PIPELINE_SA}" \
  --role="roles/cloudbuild.builds.editor" \
  --condition=None --quiet

echo "4. Granting Artifact Registry Admin (roles/artifactregistry.admin)..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${PIPELINE_SA}" \
  --role="roles/artifactregistry.admin" \
  --condition=None --quiet

echo "5. Granting Storage Admin for Cloud Build source staging (roles/storage.admin)..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${PIPELINE_SA}" \
  --role="roles/storage.admin" \
  --condition=None --quiet

# 4. Firebase Hosting Deployment Roles & APIs
echo "6. Enabling Firebase APIs (firebase.googleapis.com, firebasehosting.googleapis.com)..."
gcloud services enable firebase.googleapis.com firebasehosting.googleapis.com \
  --project="${PROJECT_ID}" --quiet || true

echo "7. Granting Firebase Hosting Admin (roles/firebasehosting.admin)..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${PIPELINE_SA}" \
  --role="roles/firebasehosting.admin" \
  --condition=None --quiet

echo "8. Granting Firebase Viewer (roles/firebase.viewer)..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${PIPELINE_SA}" \
  --role="roles/firebase.viewer" \
  --condition=None --quiet

echo ""
echo "================================================================="
echo "✅ All deployment IAM roles successfully granted to ${PIPELINE_SA}"
echo "================================================================="
