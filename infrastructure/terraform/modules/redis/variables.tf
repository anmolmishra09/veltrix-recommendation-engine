variable "name" {
  description = "Name of the Redis replication group"
  type        = string
}

variable "engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "6.2"
}

variable "node_type" {
  description = "Cache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "number_cache_clusters" {
  description = "Number of cache clusters in the replication group"
  type        = number
  default     = 1
}

variable "automatic_failover_enabled" {
  description = "Whether automatic failover is enabled"
  type        = bool
  default     = false
}

variable "port" {
  description = "Port for Redis"
  type        = number
  default     = 6379
}

variable "vpc_id" {
  description = "VPC ID where the Redis cluster will be deployed"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for the Redis subnet group"
  type        = list(string)
}

variable "maintenance_window" {
  description = "Maintenance window (e.g., 'sun:05:00-sun:06:00')"
  type        = string
  default     = "sun:05:00-sun:06:00"
}

variable "snapshot_retention_limit" {
  description = "Number of days to retain automatic snapshots"
  type        = number
  default     = 0
}

variable "snapshot_window" {
  description = "Daily time range (in UTC) during which snapshots are taken"
  type        = string
  default     = "05:00-06:00"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}