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

resource "aws_instance" "promptinfra_instance" {
  ami           = "ami-0c02fb55956c7d316"
  instance_type = "t2.micro"
  
  tags = {
    Name = "PromptInfra Instance"
    source = "promptinfra"
    auto_generated = "true"
    created_at = "2025-10-01"
    managed_by = "promptinfra"
  }
}

output "instance_ip" {
  value = aws_instance.promptinfra_instance.public_ip
}