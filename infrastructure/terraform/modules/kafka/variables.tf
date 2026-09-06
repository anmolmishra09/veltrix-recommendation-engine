variable "cluster_name" {
  description = "Name of the MSK cluster"
  type        = string
}

variable "kafka_version" {
  description = "Kafka version"
  type        = string
  default     = "2.8.1"
}

variable "number_of_broker_nodes" {
  description = "Number of broker nodes in the MSK cluster"
  type        = number
  default     = 3
}

variable "broker_instance_type" {
  description = "Instance type for MSK brokers"
  type        = string
  default     = "kafka.m5.large"
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for the MSK cluster"
  type        = list(string)
}

variable "vpc_id" {
  description = "VPC ID where the MSK cluster will be deployed"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC"
  type        = string
}

variable "tls_port" {
  description = "TLS port for MSK cluster"
  type        = number
  default     = 9094
}

variable "plaintext_port" {
  description = "Plaintext port for MSK cluster"
  type        = number
  default     = 9092
}

variable "ebs_volume_size" {
  description = "EBS volume size per broker in GB"
  type        = number
  default     = 1000
}

variable "encryption_at_rest_kms_key_arn" {
  description = "KMS key ARN for encryption at rest"
  type        = string
  default     = "" # Optional, if not provided uses default MSK key
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}