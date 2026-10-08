# Define the isolated network, SSH key pair, and single Nginx EC2 instance.

# The VPC provides the private address space for assignment resources.
resource "aws_vpc" "web" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "codyssey-b3-1-vpc"
  }
}

# Place the instance in a smaller address range and enable public IPv4 assignment.
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.web.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true

  tags = {
    Name = "codyssey-b3-1-public-subnet"
  }
}

# Attach the VPC's internet entry and exit point.
resource "aws_internet_gateway" "web" {
  vpc_id = aws_vpc.web.id

  tags = {
    Name = "codyssey-b3-1-igw"
  }
}

# Define where traffic from the public subnet is sent.
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.web.id

  # Send traffic outside the VPC through the Internet Gateway.
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.web.id
  }

  tags = {
    Name = "codyssey-b3-1-public-routes"
  }
}

# Make the public subnet use the route table containing the internet route.
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Control traffic at the instance: public HTTP, restricted SSH, and outbound internet.
resource "aws_security_group" "web" {
  name        = "codyssey-b3-1-web"
  description = "Public HTTP and SSH from the learner's IPv4 address only."
  vpc_id      = aws_vpc.web.id

  # Accept web requests from any IPv4 address on TCP port 80 only.
  ingress {
    description = "Public HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Accept SSH only from the supplied learner IPv4 /32.
  ingress {
    description = "SSH from the learner IPv4 /32"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_allowed_cidr]
  }

  # Allow outbound IPv4 traffic; protocol -1 means all IP protocols.
  egress {
    description = "Internet access for package installation and connectivity checks"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "codyssey-b3-1-web-sg"
  }
}

# Look up an existing official Ubuntu image; this data source creates no AMI.
data "aws_ami" "ubuntu" {
  # Restrict ownership to Canonical and select the newest matching image.
  most_recent = true
  owners      = ["099720109477"]

  # Match the standard Ubuntu 24.04 LTS server image, excluding Pro and minimal variants.
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  # Match the x86_64 architecture used by t3.micro.
  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  # Use hardware virtualization supported by this instance type.
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  # Require an EBS-backed root disk.
  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }

  # Only select images that are ready to launch.
  filter {
    name   = "state"
    values = ["available"]
  }
}

# Register only the local public key in AWS for later SSH access.
resource "aws_key_pair" "web" {
  key_name   = "codyssey-b3-1-web"
  public_key = trimspace(file(pathexpand(var.public_key_path)))

  tags = {
    Name = "codyssey-b3-1-web-key"
  }
}

# Launch one web server with the selected image, subnet, firewall, and SSH key.
resource "aws_instance" "web" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.web.id]
  key_name                    = aws_key_pair.web.key_name
  associate_public_ip_address = true
  # cloud-init runs this script on first boot; changes require instance replacement.
  user_data                   = file("${path.module}/user_data.sh")
  user_data_replace_on_change = true

  # Encrypt the 8 GiB root disk and delete it when the instance terminates.
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 8
    encrypted             = true
    delete_on_termination = true

    tags = {
      Name    = "codyssey-b3-1-root-volume"
      Project = "codyssey-b3-1"
    }
  }

  # Standard mode prevents charges for surplus CPU credits.
  credit_specification {
    cpu_credits = "standard"
  }

  # Require token-based IMDSv2 requests for instance metadata.
  metadata_options {
    http_tokens = "required"
  }

  # Package installation needs the Internet Gateway route before boot.
  depends_on = [aws_route_table_association.public]

  tags = {
    Name = "codyssey-b3-1-web"
  }
}
