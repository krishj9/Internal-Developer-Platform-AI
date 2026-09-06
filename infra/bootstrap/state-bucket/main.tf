resource "google_storage_bucket" "state_bucket" {
  name          = var.bucket_name
  project       = var.project_id
  location      = var.location
  force_destroy = false

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      num_newer_versions = 10
      with_state         = "ARCHIVED"
    }
  }

  labels = merge(var.labels, {
    managed_by = "idp-platform"
    purpose    = "terraform-state"
  })
}
