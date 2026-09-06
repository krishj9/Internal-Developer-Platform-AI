# Runbook: End-of-POC Complete Teardown (Destroy All)

## 1. Overview
This procedure safely destroys all active agent workloads, cleans up cloud infrastructure, removes remote state, and terminates project billing.

---

## 2. Step 1: Automated Workload Teardown
Run the automated cleanup endpoint to queue destruction for all active deployments:
```bash
ADMIN_TOKEN=$(idp login -u admin_gov -p "..." --url "http://localhost:8000" && cat ~/.idp/session.json | jq -r .token)

# Query and dispatch destroy for all active deployments
curl -X POST http://localhost:8000/governance/cleanup-expired \
  -H "Authorization: Bearer ${ADMIN_TOKEN}"
```

---

## 3. Step 2: Delete Remote State & Bootstrap Buckets
```bash
# Empty state bucket objects
gcloud storage rm --recursive gs://idp-poc-state-${PROJECT_ID}/**

# Delete state bucket
gcloud storage buckets delete gs://idp-poc-state-${PROJECT_ID}
```

---

## 4. Step 3: Remove Service Accounts & Workload Identity Pool
```bash
gcloud iam workload-identity-pools delete idp-pool --location=global --quiet

gcloud iam service-accounts delete idp-api-runtime@${PROJECT_ID}.iam.gserviceaccount.com --quiet
gcloud iam service-accounts delete idp-pipeline-t1-dev@${PROJECT_ID}.iam.gserviceaccount.com --quiet
gcloud iam service-accounts delete idp-pipeline-t2-dev@${PROJECT_ID}.iam.gserviceaccount.com --quiet
gcloud iam service-accounts delete idp-pipeline-t3-dev@${PROJECT_ID}.iam.gserviceaccount.com --quiet
```
