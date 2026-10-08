output "public_ip" {
  description = "Instance public IPv4 address."
  value       = aws_instance.web.public_ip
}

output "root_url" {
  description = "Static Hello Cloud page URL."
  value       = "http://${aws_instance.web.public_ip}/"
}

output "health_url" {
  description = "External health endpoint URL."
  value       = "http://${aws_instance.web.public_ip}/health"
}

output "instance_id" {
  description = "EC2 instance ID for validation and cleanup."
  value       = aws_instance.web.id
}

output "root_volume_id" {
  description = "Root EBS volume ID for deletion verification."
  value       = aws_instance.web.root_block_device[0].volume_id
}

output "vpc_id" {
  description = "Assignment VPC ID."
  value       = aws_vpc.web.id
}

output "subnet_id" {
  description = "Public subnet ID."
  value       = aws_subnet.public.id
}

output "route_table_id" {
  description = "Public route table ID."
  value       = aws_route_table.public.id
}

output "internet_gateway_id" {
  description = "Internet Gateway ID."
  value       = aws_internet_gateway.web.id
}

output "security_group_id" {
  description = "Web Security Group ID."
  value       = aws_security_group.web.id
}

output "key_pair_name" {
  description = "AWS key pair name for deletion verification."
  value       = aws_key_pair.web.key_name
}
