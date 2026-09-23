#This table stores the result of each check of the site.
#Each row is identified by the check type (availability/latency/content) and the test date

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
