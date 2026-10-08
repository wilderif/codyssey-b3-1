variable "aws_profile" {
  description = "Named local AWS CLI profile for the dedicated assignment IAM user."
  type        = string
  nullable    = false

  validation {
    condition     = trimspace(var.aws_profile) != ""
    error_message = "aws_profile must be a non-empty local AWS CLI profile name."
  }
}

variable "ssh_allowed_cidr" {
  description = "Learner's IPv4 address with a /32 prefix for SSH access."
  type        = string
  nullable    = false

  validation {
    condition = (
      can(cidrnetmask(var.ssh_allowed_cidr)) &&
      can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+/32$", var.ssh_allowed_cidr))
    )
    error_message = "ssh_allowed_cidr must be a single valid IPv4 /32, such as 203.0.113.10/32."
  }
}

variable "public_key_path" {
  description = "Path to the dedicated RSA or ED25519 OpenSSH public key; keep the private key outside the repository."
  type        = string
  nullable    = false

  validation {
    # Reject private key contents before they can be passed to an AWS resource.
    condition = can(regex(
      "^(ssh-rsa|ssh-ed25519) [A-Za-z0-9+/]+={0,2}( [^\\r\\n]*)?$",
      trimspace(file(pathexpand(var.public_key_path)))
    ))
    error_message = "public_key_path must point to a readable RSA or ED25519 OpenSSH public key file."
  }
}
