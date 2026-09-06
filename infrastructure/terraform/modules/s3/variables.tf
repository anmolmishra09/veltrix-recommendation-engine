variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "acl" {
  description = "ACL for the bucket (e.g., private, public-read)"
  type        = string
  default     = "private"
}

variable "versioning_enabled" {
  description = "Whether versioning is enabled"
  type        = bool
  default     = true
}

variable "sse_algorithm" {
  description = "Server-side encryption algorithm (e.g., AES256, aws:kms)"
  type        = string
  default     = "AES256"
}

variable "lifecycle_enabled" {
  description = "Whether lifecycle rules are enabled"
  type        = bool
  default     = false
}

variable "expiration_days" {
  description = "Number of days after which objects expire"
  type        = number
  default     = 365
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}