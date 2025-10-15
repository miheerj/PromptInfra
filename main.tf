terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "main" {
  ami           = "ami-0c02fb55956c7d316"  # Amazon Linux 2
  instance_type = "t2.micro"
  
  tags = {
    Name        = "PromptInfra Instance"
    ManagedBy   = "promptinfra"
    CreatedAt   = "2025-10-14"
    Environment = "development"
  }
}

output "instance_ip" {
  value       = aws_instance.main.public_ip
  description = "Public IP of the instance"
}