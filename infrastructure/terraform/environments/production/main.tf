provider "aws" {
  region = var.aws_region
}

# Networking Module
module "networking" {
  source = "../../modules/networking"

  name                 = var.environment_name
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  tags = var.common_tags
}

# EKS Module
module "eks" {
  source = "../../modules/eks"

  cluster_name           = var.environment_name
  kubernetes_version     = var.kubernetes_version
  private_subnet_ids     = module.networking.private_subnet_ids
  instance_types         = var.eks_instance_types
  node_group_desired_size= var.eks_node_group_desired_size
  node_group_max_size    = var.eks_node_group_max_size
  node_group_min_size    = var.eks_node_group_min_size
  tags = var.common_tags
}

# RDS Module
module "rds" {
  source = "../../modules/rds"

  name                 = var.environment_name
  engine_version       = var.rds_engine_version
  instance_class       = var.rds_instance_class
  allocated_storage    = var.rds_allocated_storage
  database_name        = var.rds_database_name
  username             = var.rds_username
  password             = var.rds_password
  skip_final_snapshot  = var.rds_skip_final_snapshot
  vpc_id               = module.networking.vpc_id
  vpc_cidr             = var.vpc_cidr
  private_subnet_ids   = module.networking.private_subnet_ids
  tags = var.common_tags
}

# Redis Module
module "redis" {
  source = "../../modules/redis"

  name                 = var.environment_name
  engine_version       = var.redis_engine_version
  node_type            = var.redis_node_type
  number_cache_clusters= var.redis_number_cache_clusters
  automatic_failover_enabled = var.redis_automatic_failover_enabled
  vpc_id               = module.networking.vpc_id
  vpc_cidr             = var.vpc_cidr
  private_subnet_ids   = module.networking.private_subnet_ids
  tags = var.common_tags
}

# Kafka Module
module "kafka" {
  source = "../../modules/kafka"

  cluster_name           = var.environment_name
  kafka_version          = var.kafka_version
  number_of_broker_nodes = var.kafka_number_of_broker_nodes
  broker_instance_type   = var.kafka_broker_instance_type
  private_subnet_ids     = module.networking.private_subnet_ids
  vpc_id                 = module.networking.vpc_id
  vpc_cidr               = var.vpc_cidr
  tags = var.common_tags
}

# S3 Module
module "s3" {
  source = "../../modules/s3"

  bucket_name          = var.s3_bucket_name
  acl                  = var.s3_acl
  versioning_enabled   = var.s3_versioning_enabled
  sse_algorithm        = var.s3_sse_algorithm
  lifecycle_enabled    = var.s3_lifecycle_enabled
  expiration_days      = var.s3_expiration_days
  tags = var.common_tags
}

# IAM Module (example for a specific role)
module "iam_role" {
  source = "../../modules/iam"

  name = "${var.environment_name}-app-role"
  assume_role_policy_json = data.aws_iam_policy_document.ec2_assume_role.json
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
    "arn:aws:iam::aws:policy/CloudWatchFullAccess"
  ]
  tags = var.common_tags
}

# Data for IAM assume role policy
data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

# Monitoring Module (example alarms)
module "monitoring" {
  source = "../../modules/monitoring"

  alarms = {
    high_cpu_eks = {
      alarm_name          = "${var.environment_name}-high-cpu-eks"
      comparison_operator = "GreaterThanThreshold"
      evaluation_periods  = 2
      metric_name         = "CPUUtilization"
      namespace           = "AWS/EKS"
      period              = 300
      statistic           = "Average"
      threshold           = 80
      alarm_description   = "Alarm when CPU utilization exceeds 80% for 2 periods"
      dimensions = {
        ClusterName = module.eks.cluster_name
      }
      alarm_actions       = [var.alert_sns_topic]
      ok_actions          = [var.alert_sns_topic]
      insufficient_data_actions = [var.alert_sns_topic]
    }
  }

  tags = var.common_tags
}