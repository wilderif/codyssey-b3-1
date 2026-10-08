# Define compatible Terraform and provider versions for this configuration.
terraform {
  # Keep the Terraform CLI within the supported major version.
  required_version = ">= 1.15, < 2.0"

  # The AWS provider translates resource definitions into AWS API operations.
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
