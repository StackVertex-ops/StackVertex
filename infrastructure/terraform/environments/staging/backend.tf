# Automatisch generiert durch bootstrap Workflow
terraform {
  backend "s3" {
    bucket         = "stackvertex-terraform-state-302659227737"
    key            = "staging/terraform.tfstate"
    region         = "eu-central-1"
    dynamodb_table = "stackvertex-terraform-locks"
    encrypt        = true
  }
}
