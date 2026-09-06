output "alarm_names" {
  description = "List of alarm names created"
  value       = [for k, v in aws_cloudwatch_metric_alarm.this : v.alarm_name]
}