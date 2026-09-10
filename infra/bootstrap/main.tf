data "aws_caller_identity" "current" {}

#Le bucket stock uniquement le fichier d'état Terraform
#Il est géré à part puisqu'il ne peut pas servir de backend à lui-même
resource "aws_s3_bucket" "terraform_state" {
  bucket = "${var.project_name}-tfstate-${data.aws_caller_identity.current.account_id}"

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
    Purpose   = "terraform-state"
  }
}
#versionning
#Le but est de garder les anciennes versions du state.
#Si un apply casse quelque chose ou si le state est supprimé par erreur ça permet de revenir en arrière
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

#Chiffrement
#Le state peut contenir des infos sensibles comme IDs de ressources, métadonnées ect.
#On utilise le chiffrement pour protèger les infos sensibles si le bucket venait à être exposé.
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
#Blocage d'accès public
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

#Empêche que deux terraform apply tournent en même temps et compromettent le state.
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "${var.project_name}-tfstate-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
    Purpose   = "terraform-state-lock"
  }
}
