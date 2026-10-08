# Expose connection details and resource identifiers for verification and cleanup.

# Use this address for browser, curl, and SSH access after provisioning.
output "public_ip" {
  description = "Instance public IPv4 address."
  value       = aws_instance.web.public_ip
}

# Open the static page in a browser.
output "root_url" {
  description = "Static Hello Cloud page URL."
  value       = "http://${aws_instance.web.public_ip}/"
}

# Use this endpoint for the assignment's external HTTP verification (method B).
output "health_url" {
  description = "External health endpoint URL."
  value       = "http://${aws_instance.web.public_ip}/health"
}

# Identify the EC2 instance when checking its state and final termination.
output "instance_id" {
  description = "EC2 instance ID for validation and cleanup."
  value       = aws_instance.web.id
}

# Verify that the root volume is deleted after instance termination.
output "root_volume_id" {
  description = "Root EBS volume ID for deletion verification."
  value       = aws_instance.web.root_block_device[0].volume_id
}

# Identify the network boundary when verifying final VPC removal.
output "vpc_id" {
  description = "Assignment VPC ID."
  value       = aws_vpc.web.id
}

# Identify the subnet containing the web server.
output "subnet_id" {
  description = "Public subnet ID."
  value       = aws_subnet.public.id
}

# Inspect the default internet route and verify route table deletion.
output "route_table_id" {
  description = "Public route table ID."
  value       = aws_route_table.public.id
}

# Check the gateway's VPC attachment and final deletion.
output "internet_gateway_id" {
  description = "Internet Gateway ID."
  value       = aws_internet_gateway.web.id
}

# Inspect allowed traffic sources and verify security group deletion.
output "security_group_id" {
  description = "Web Security Group ID."
  value       = aws_security_group.web.id
}

# Identify the AWS key pair; local key files need separate cleanup.
output "key_pair_name" {
  description = "AWS key pair name for deletion verification."
  value       = aws_key_pair.web.key_name
}
