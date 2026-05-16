# Provider Configuration for Cross-Region Backup
#
# This module requires an aliased provider for the DR region
# The calling module must configure:
#
# provider "aws" {
#   alias  = "secondary"
#   region = "eu-west-1"  # DR region
# }
#
# And pass it to this module:
#
# module "backup" {
#   source = "../../modules/backup"
#   providers = {
#     aws.secondary = aws.secondary
#   }
#   ...
# }

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
      configuration_aliases = [
        aws.secondary
      ]
    }
  }
}
