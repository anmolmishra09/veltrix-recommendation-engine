variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment_name" {
  description = "Name of the environment (e.g., dev, staging, prod)"
  type        = string
  default     = "staging"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "List of public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "List of private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "eks_instance_types" {
  description = "List of instance types for EKS node group"
  type        = list(string)
  default     = ["t3.large"] # Larger than dev
}

variable "eks_node_group_desired_size" {
  description = "Desired number of nodes in the EKS node group"
  type        = number
  default     = 3
}

variable "eks_node_group_max_size" {
  description = "Maximum number of nodes in the EKS node group"
  type        = number
  default     = 5
}

variable "eks_node_group_min_size" {
  description = "Minimum number of nodes in the EKS node group"
  type        = number
  default     = 2
}

variable "kubernetes_version" {
  description = "Kubernetes version for EKS"
  type        = string
  default     = "1.21"
}

variable "rds_engine_version" {
  description = "PostgreSQL engine version for RDS"
  type        = string
  default     = "13.7"
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.large" # Larger than dev
}

variable "rds_allocated_storage" {
  description = "Allocated storage for RDS in GB"
  type        = number
  default     = 50 # Larger than dev
}

variable "rds_database_name" {
  description = "Database name for RDS"
  type        = string
  default     = "recommendation_db"
}

variable "rds_username" {
  description = "Username for RDS"
  type        = string
}

variable "rds_password" {
  description = "Password for RDS"
  type        = string
  sensitive   = true
}

variable "rds_skip_final_snapshot" {
  description = "Whether to skip final snapshot when deleting RDS instance"
  type        = bool
  default     = true
}

variable "redis_engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "6.2"
}

variable "redis_node_type" {
  description = "Redis node type"
  type        = string
  default     = "cache.t3.medium" # Larger than dev
}

variable "redis_number_cache_clusters" {
  description = "Number of Redis cache clusters"
  type        = number
  default     = 1
}

variable "redis_automatic_failover_enabled" {
  description = "Whether automatic failover is enabled for Redis"
  type        = bool
  default     = false
}

variable "kafka_version" {
  description = "Kafka version for MSK"
  type        = string
  default     = "2.8.1"
}

variable "kafka_number_of_broker_nodes" {
  description = "Number of broker nodes in MSK cluster"
  type        = number
  default     = 3
}

variable "kafka_broker_instance_type" {
  description = "Instance type for MSK brokers"
  type        = string
  default     = "kafka.m5.large"
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "s3_acl" {
  description = "ACL for the S3 bucket"
  type        = string
  default     = "private"
}

variable "s3_versioning_enabled" {
  description = "Whether versioning is enabled for the S3 bucket"
  type        = bool
  default     = true
}

variable "s3_sse_algorithm" {
  description = "Server-side encryption algorithm for S3"
  type        = string
  default     = "AES256"
}

variable "s3_lifecycle_enabled" {
  description = "Whether lifecycle rules are enabled for the S3 bucket"
  type        = bool
  default     = false
}

variable "s3_expiration_days" {
  description = "Number of days after which objects expire in S3"
  type        = number
  default     = 365
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "staging"
  }
}

variable "alert_sns_topic" {
  description = "SNS topic ARN for alerts"
  type        = string
  default     = ""
}