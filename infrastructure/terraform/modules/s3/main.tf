# S3 Bucket
resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name
  acl    = var.acl

  tags = var.tags

  versioning {
    enabled = var.versioning_enabled
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = var.sse_algorithm
      }
    }
  }

  lifecycle_rule {
    id      = "expire-old-objects"
    enabled = var.lifecycle_enabled

    expiration {
      days = var.expiration_days
    }
  }
}

# S3 Bucket Policy (optional, for example to allow public read if needed)
resource "aws_s3_bucket_policy" "public_read" {
  count = var.acl == "public-read" ? 1 : 0
  bucket = aws_s3_bucket.this.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = "*"
        Action    = [
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.this.arn}/*"
      }
    ]
  })
}