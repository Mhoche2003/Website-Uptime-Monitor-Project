output "website_endpoint" {
  value = "http://${aws_s3_bucket.dashboard.bucket}.s3-website-${var.aws_region}.amazonaws.com"
}

output "bucket_name" {
  value = aws_s3_bucket.dashboard.id
}

output "bucket_arn" {
  value = aws_s3_bucket.dashboard.arn
}
