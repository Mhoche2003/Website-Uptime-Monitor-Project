# Stores every check result, so the dashboard can compute uptime %,
# average response time and recent incidents.
#
# Key design: hash_key = check_type ("availability" | "latency" | "content"),
# range_key = timestamp (ISO 8601). This lets us query "all results of one
# check type, ordered by time" directly, which is exactly what the dashboard
# needs, with no secondary index.
resource "aws_dynamodb_table" "history" {
  name         = "${var.project_name}-check-history"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "check_type"
  range_key    = "timestamp"

  attribute {
    name = "check_type"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = var.tags
}
