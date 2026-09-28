resource "aws_s3_bucket" "site" {
  bucket = "${var.project_name}-site"

  tags = var.tags
}

resource "aws_s3_bucket_website_configuration" "site" {
  bucket = aws_s3_bucket.site.id

  index_document {
    suffix = "index.html"
  }
}

resource "aws_s3_bucket_public_access_block" "site" {
  bucket = aws_s3_bucket.site.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "site" {
  bucket = aws_s3_bucket.site.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.site.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.site]
}

# index.html uses a template so the hidden marker comment stays in sync with
# var.site_marker_text, the same value check_content compares against.
resource "aws_s3_object" "index" {
  bucket       = aws_s3_bucket.site.id
  key          = "index.html"
  content_type = "text/html"
  content = templatefile("${path.module}/site/index.html.tftpl", {
    site_marker_text = var.site_marker_text
  })
}

# The other 3 pages are static, no variable to inject, so they're uploaded as-is.
# etag tracks the file's content hash, so Terraform re-uploads when the file changes.
resource "aws_s3_object" "about" {
  bucket       = aws_s3_bucket.site.id
  key          = "about.html"
  content_type = "text/html"
  source       = "${path.module}/site/about.html"
  etag         = filemd5("${path.module}/site/about.html")
}

resource "aws_s3_object" "contact" {
  bucket       = aws_s3_bucket.site.id
  key          = "contact.html"
  content_type = "text/html"
  source       = "${path.module}/site/contact.html"
  etag         = filemd5("${path.module}/site/contact.html")
}

resource "aws_s3_object" "legal" {
  bucket       = aws_s3_bucket.site.id
  key          = "legal.html"
  content_type = "text/html"
  source       = "${path.module}/site/legal.html"
  etag         = filemd5("${path.module}/site/legal.html")
}
