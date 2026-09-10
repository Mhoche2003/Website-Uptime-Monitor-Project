#Cette table stocke le résultat de chaque check du site.
#Chaque ligne est identifiée par le type de check (availability/latency/content) et la date du test

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
