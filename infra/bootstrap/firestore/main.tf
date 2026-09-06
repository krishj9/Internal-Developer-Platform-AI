resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = var.database_id
  location_id = var.location_id
  type        = "FIRESTORE_NATIVE"

  concurrency_mode                  = "OPTIMISTIC"
  app_engine_integration_mode       = "DISABLED"
  point_in_time_recovery_enablement = "POINT_IN_TIME_RECOVERY_ENABLED"
  delete_protection_state           = "DELETE_PROTECTION_DISABLED" # Can be enabled for production
  deletion_policy                   = "ABANDON"
}
