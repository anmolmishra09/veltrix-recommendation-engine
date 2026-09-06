# IAM Role
resource "aws_iam_role" "this" {
  name = var.name

  assume_role_policy = var.assume_role_policy_json
  tags               = var.tags
}

# Attach managed policies
resource "aws_iam_role_policy_attachment" "managed" {
  for_each = toset(var.managed_policy_arns)
  role     = aws_iam_role.this.name
  policy_arn = each.value
}

# Create and attach inline policies
resource "aws_iam_policy" "inline" {
  for_each = var.inline_policies
  name     = "${var.name}-${each.key}"
  policy   = each.value
}

resource "aws_iam_role_policy" "inline" {
  for_each = aws_iam_policy.inline
  role     = aws_iam_role.this.id
  policy   = each.value.id
}