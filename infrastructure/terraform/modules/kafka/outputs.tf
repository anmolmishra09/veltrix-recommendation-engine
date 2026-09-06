output "bootstrap_brokers_tls" {
  description = "Bootstrap brokers for TLS"
  value       = aws_msk_cluster.this.bootstrap_brokers_tls
}

output "bootstrap_brokers" {
  description = "Bootstrap brokers (plaintext)"
  value       = aws_msk_cluster.this.bootstrap_brokers
}

output "cluster_arn" {
  description = "ARN of the MSK cluster"
  value       = aws_msk_cluster.this.arn
}