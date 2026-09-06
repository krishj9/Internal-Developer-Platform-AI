terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable Required GCP APIs
locals {
  required_services = [
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "storage.googleapis.com",
    "firestore.googleapis.com",
    "secretmanager.googleapis.com",
    "run.googleapis.com",
    "aiplatform.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "pubsub.googleapis.com",
  ]
}

resource "google_project_service" "services" {
  for_each                   = toset(local.required_services)
  project                    = var.project_id
  service                    = each.key
  disable_dependent_services = false
  disable_on_destroy         = false
}

# 2. State Bucket Module
module "state_bucket" {
  source      = "./state-bucket"
  project_id  = var.project_id
  bucket_name = var.state_bucket_name
  labels      = var.labels

  depends_on = [google_project_service.services]
}

# 3. Firestore Native Database Module
module "firestore" {
  source      = "./firestore"
  project_id  = var.project_id
  location_id = var.firestore_location_id
  database_id = var.firestore_database_id

  depends_on = [google_project_service.services]
}

# 4. Service Accounts Module
module "service_accounts" {
  source            = "./service-accounts"
  project_id        = var.project_id
  state_bucket_name = module.state_bucket.bucket_name
  environment       = var.environment

  depends_on = [google_project_service.services]
}

# 5. Secret Manager Secret Containers Module
module "secret_manager" {
  source               = "./secret-manager"
  project_id           = var.project_id
  api_runtime_sa_email = module.service_accounts.api_runtime_sa_email
  labels               = var.labels

  depends_on = [google_project_service.services]
}

# 6. Workload Identity Federation Module
module "workload_identity" {
  source            = "./workload-identity"
  project_id        = var.project_id
  github_repository = var.github_repository
  pipeline_sa_email = module.service_accounts.pipeline_t1_dev_sa_email

  depends_on = [google_project_service.services]
}
