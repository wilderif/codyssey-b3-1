# Configure AWS access through a local profile; credentials stay outside the repository.
provider "aws" {
  # All regional resources use Seoul and the explicitly supplied profile.
  region  = "ap-northeast-2"
  profile = var.aws_profile

  # Apply a common project tag to supported resources for cleanup tracking.
  default_tags {
    tags = {
      Project = "codyssey-b3-1"
    }
  }
}
