# Runbook: Secret & Signing Key Rotation

## 1. Rotating JWT Signing Key
The JWT signing key (`idp-jwt-signing-key`) can be rotated with zero control plane disruption.

1. Generate new 32-byte secret key:
   ```bash
   NEW_KEY=$(openssl rand -hex 32)
   ```
2. Add new version to Google Secret Manager:
   ```bash
   echo -n "${NEW_KEY}" | gcloud secrets versions add idp-jwt-signing-key --data-file=-
   ```
3. Restart Cloud Run API instances to load the latest secret version:
   ```bash
   gcloud run services update idp-api --update-env-vars ROTATED_AT=$(date +%s)
   ```
4. Optional: To force global re-login for all active users, increment `token_version` on all user records in Firestore.

---

## 2. Rotating GitHub Dispatch Token
1. Generate fine-grained GitHub PAT with `Actions: Read and write` permission on repository.
2. Add new version in Secret Manager:
   ```bash
   echo -n "${NEW_PAT}" | gcloud secrets versions add idp-github-dispatch-token --data-file=-
   ```
3. Destroy the old PAT in GitHub Settings -> Developer settings.
