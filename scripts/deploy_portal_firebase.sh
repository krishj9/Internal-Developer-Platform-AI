#!/usr/bin/env bash
# ==============================================================================
# Deploy Portal to Firebase Hosting
# ==============================================================================
# Builds the production React bundle and deploys to Firebase Hosting site idp4gcp.
# Uses npx firebase-tools on-the-fly (no global firebase-tools installation needed).
#
# Usage:
#   bash scripts/deploy_portal_firebase.sh [PROJECT_ID] [API_URL]
# ==============================================================================

set -euo pipefail

PROJECT_ID="${1:-${GCP_PROJECT:-mybrightday-dev}}"
API_URL="${2:-https://idp-api-754915077075.us-central1.run.app}"
SITE_NAME="idp4gcp"

echo "================================================================="
echo "🚀 Deploying Portal to Firebase Hosting: ${SITE_NAME}.web.app"
echo "================================================================="
echo "  • GCP Project:   ${PROJECT_ID}"
echo "  • Hosting Site:  ${SITE_NAME}"
echo "  • API Base URL:  ${API_URL}"
echo "================================================================="
echo ""

# 1. Build the production React bundle
echo "Step 1: Installing portal dependencies and building bundle..."
(
  cd portal
  npm ci
  VITE_API_URL="${API_URL}" npm run build
)

# 2. Deploy using npx firebase-tools
echo ""
echo "Step 2: Deploying to Firebase Hosting via npx firebase-tools..."
npx firebase-tools deploy \
  --only hosting \
  --project "${PROJECT_ID}"

echo ""
echo "================================================================="
echo "✅ Portal successfully deployed to: https://${SITE_NAME}.web.app"
echo "================================================================="
