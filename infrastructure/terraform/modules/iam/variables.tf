variable "name" {
  description = "Name of the IAM role"
  type        = string
}

variable "assume_role_policy_json" {
  description = "JSON policy document that defines who can assume the role"
  type        = string
}

variable "managed_policy_arns" {
  description = "List of ARN's of IAM managed policies to attach"
  type        = list(string)
  default     = []
}

variable "inline_policies" {
  description = "Map of inline policy names to JSON policy documents"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}