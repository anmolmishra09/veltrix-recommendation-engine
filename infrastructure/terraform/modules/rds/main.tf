# RDS Subnet Group
resource "aws_db_subnet_group" "this" {
  name       = "${var.name}-subnet-group"
  subnet_ids = var.private_subnet_ids
  tags = var.tags
}

# RDS Security Group
resource "aws_security_group" "this" {
  name        = "${var.name}-sg"
  description = "Allow inbound traffic from the VPC"
  vpc_id      = var.vpc_id

  ingress {
    description = "PostgreSQL from VPC"
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

# RDS Instance
resource "aws_db_instance" "this" {
  identifier          = var.name
  engine              = "postgres"
  engine_version      = var.engine_version
  instance_class      = var.instance_class
  allocated_storage   = var.allocated_storage
  name                = var.database_name
  username            = var.username
  password            = var.password
  skip_final_snapshot = var.skip_final_snapshot
  subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.this.id]
  tags = var.tags
}