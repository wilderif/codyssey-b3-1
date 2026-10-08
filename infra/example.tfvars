# Non-secret input examples; replace them with local values in an ignored .tfvars file.

# Name of the AWS CLI profile for the dedicated assignment IAM user.
aws_profile = "codyssey-assignment"

# Example-only address; replace it with your current public IPv4 followed by /32.
ssh_allowed_cidr = "203.0.113.10/32"

# Public key path; keep the corresponding private key outside the repository.
public_key_path = "~/.ssh/codyssey-assignment.pub"
