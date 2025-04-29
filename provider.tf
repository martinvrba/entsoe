provider "aws" {
  region = "eu-north-1"
}

terraform {
  backend "s3" {
    bucket  = "entsoe-terraform-state"
    key     = "terraform.tfstate"
    region  = "eu-north-1"
    encrypt = true
  }
}
