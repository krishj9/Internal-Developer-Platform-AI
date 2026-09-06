output "database_name" {
  value       = google_firestore_database.database.name
  description = "The name of the Firestore Native database"
}

output "location_id" {
  value       = google_firestore_database.database.location_id
  description = "The location ID of the Firestore database"
}
