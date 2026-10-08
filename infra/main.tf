resource "aws_vpc" "web" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "codyssey-b3-1-vpc"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.web.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true

  tags = {
    Name = "codyssey-b3-1-public-subnet"
  }
}

resource "aws_internet_gateway" "web" {
  vpc_id = aws_vpc.web.id

  tags = {
    Name = "codyssey-b3-1-igw"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.web.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.web.id
  }

  tags = {
    Name = "codyssey-b3-1-public-routes"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "web" {
  name        = "codyssey-b3-1-web"
  description = "Public HTTP and SSH from the learner's IPv4 address only."
  vpc_id      = aws_vpc.web.id

  ingress {
    description = "Public HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH from the learner's IPv4 /32"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_allowed_cidr]
  }

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

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

resource "aws_key_pair" "web" {
  key_name   = "codyssey-b3-1-web"
  public_key = trimspace(file(pathexpand(var.public_key_path)))

  tags = {
    Name = "codyssey-b3-1-web-key"
  }
}

resource "aws_instance" "web" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.web.id]
  key_name                    = aws_key_pair.web.key_name
  associate_public_ip_address = true
  user_data                   = file("${path.module}/user_data.sh")
  user_data_replace_on_change = true

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

  credit_specification {
    cpu_credits = "standard"
  }

  metadata_options {
    http_tokens = "required"
  }

  # Package installation needs the Internet Gateway route before boot.
  depends_on = [aws_route_table_association.public]

  tags = {
    Name = "codyssey-b3-1-web"
  }
}
