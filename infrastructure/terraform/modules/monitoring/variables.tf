variable "alarms" {
  description = "Map of CloudWatch alarms to create"
  type        = map(object({
    alarm_name                  = string
    comparison_operator         = string
    evaluation_periods          = number
    metric_name                 = string
    namespace                   = string
    period                      = number
    statistic                   = string
    threshold                   = number
    alarm_description           = string
    dimensions                  = map(string)
    alarm_actions               = list(string)
    ok_actions                  = list(string)
    insufficient_data_actions   = list(string)
  }))
  default = {}
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}