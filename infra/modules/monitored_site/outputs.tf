output "website_endpoint" {
  value = "http://${aws_s3_bucket.site.bucket}.s3-website-${var.aws_region}.amazonaws.com"
}

output "bucket_name" {
  value = aws_s3_bucket.site.id
}
