terraform {
  required_version = ">= 1.13.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "website-uptime-monitor-tfstate-000000000000"
    key            = "state/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "website-uptime-monitor-tfstate-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}
