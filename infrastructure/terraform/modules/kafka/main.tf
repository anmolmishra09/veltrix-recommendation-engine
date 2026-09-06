# MSK Subnet Group (not a thing, we'll use subnets directly)
# MSK Security Group
resource "aws_security_group" "this" {
  name        = "${var.name}-sg"
  description = "Allow inbound traffic on Kafka ports"
  vpc_id      = var.vpc_id

  ingress {
    description = "Kafka from VPC"
    from_port   = var.tls_port
    to_port     = var.tls_port
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  ingress {
    description = "Kafka plaintext from VPC"
    from_port   = var.plaintext_port
    to_port     = var.plaintext_port
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

# MSK Cluster
resource "aws_msk_cluster" "this" {
  cluster_name           = var.cluster_name
  kafka_version          = var.kafka_version
  number_of_broker_nodes = var.number_of_broker_nodes

  broker_node_group_info {
    instance_type        = var.broker_instance_type
    client_subnets       = var.private_subnet_ids
    security_groups      = [aws_security_group.this.id]
    storage_info {
      ebs_storage {
        volume_size = var.ebs_volume_size
      }
    }
  }

  encryption_info {
    encryption_at_rest_kms_key_arn = var.encryption_at_rest_kms_key_arn
  }

  tags = var.tags
}