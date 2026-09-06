output "primary_endpoint_address" {
  description = "The primary endpoint address of the Redis replication group"
  value       = aws_elasticache_replication_group.this.primary_endpoint_address
}

output "port" {
  description = "The port of the Redis replication group"
  value       = aws_elasticache_replication_group.this.port
}

output "replication_group_id" {
  description = "The Redis replication group ID"
  value       = aws_elasticache_replication_group.this.id
}