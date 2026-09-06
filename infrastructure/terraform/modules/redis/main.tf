# Redis Subnet Group
resource "aws_elasticache_subnet_group" "this" {
  name       = "${var.name}-subnet-group"
  subnet_ids = var.private_subnet_ids
  tags = var.tags
}

# Redis Security Group
resource "aws_security_group" "this" {
  name        = "${var.name}-sg"
  description = "Allow inbound traffic on Redis port"
  vpc_id      = var.vpc_id

  ingress {
    description = "Redis from VPC"
    from_port   = var.port
    to_port     = var.port
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

# Redis Replication Group (for cluster mode disabled) or Cluster (for enabled)
# We'll create a simple Redis instance (not clustered) for simplicity
resource "aws_elasticache_replication_group" "this" {
  replication_group_id          = var.name
  description                   = "Redis replication group for recommendation platform"
  engine                        = "redis"
  engine_version                = var.engine_version
  node_type                     = var.node_type
  number_cache_clusters         = var.number_cache_clusters
  automatic_failover_enabled    = var.automatic_failover_enabled
  port                          = var.port
  subnet_group_name             = aws_elasticache_subnet_group.this.name
  security_group_ids            = [aws_security_group.this.id]
  maintenance_window            = var.maintenance_window
  snapshot_retention_limit      = var.snapshot_retention_limit
  snapshot_window               = var.snapshot_window
  tags = var.tags
}