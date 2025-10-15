#!/usr/bin/env python3
"""
PromptInfra - Minimal AI-to-IaC Prototype
Converts natural language → Terraform → Terraform Cloud

Usage:
    python promptinfra_minimal.py "Create an EC2 instance for development"
"""

import os
import sys
import json
import hashlib
import requests
from pathlib import Path
from datetime import datetime

class PromptInfra:
    def __init__(self):
        # API Keys
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.tf_token = os.getenv('TF_API_TOKEN')
        self.tf_org = os.getenv('TF_ORGANIZATION', 'your-org-name')
        self.tf_workspace = os.getenv('TF_WORKSPACE', 'promptinfra-workspace')
        
        # Simple local cache
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Validate configuration
        if not self.openai_key:
            print("⚠️  OPENAI_API_KEY not set - will use fallback templates")
        if not self.tf_token:
            print("⚠️  TF_API_TOKEN not set - will only generate local files")
    
    def generate_terraform(self, prompt: str) -> str:
        """Generate Terraform code from natural language prompt"""
        
        # Check cache first
        cache_key = hashlib.sha256(prompt.encode()).hexdigest()[:12]
        cache_file = self.cache_dir / f"{cache_key}.tf"
        
        if cache_file.exists():
            print(f"✅ Using cached Terraform (key: {cache_key})")
            return cache_file.read_text()
        
        print(f"🤖 Generating Terraform for: {prompt}")
        
        # Try AI generation
        if self.openai_key:
            terraform_code = self._call_openai(prompt)
        else:
            terraform_code = self._fallback_template(prompt)
        
        if not terraform_code:
            raise Exception("Failed to generate Terraform code")
        
        # Cache it
        cache_file.write_text(terraform_code)
        print(f"💾 Cached Terraform (key: {cache_key})")
        
        return terraform_code
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API to generate Terraform"""
        
        system_prompt = """You are a Terraform expert. Generate AWS infrastructure code from natural language.

REQUIREMENTS:
1. Return ONLY valid Terraform HCL code - no explanations or markdown
2. Use AWS provider version ~> 5.0
3. Add these tags to ALL resources:
   - Name = descriptive name
   - ManagedBy = "promptinfra"
   - CreatedAt = current date
   - Environment = "development"
4. Follow Terraform best practices
5. Use appropriate instance types and configurations

Example structure:
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

resource "..." "..." {
  # Resource configuration with tags
}"""

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Generate Terraform for: {prompt}"}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                return self._clean_code(content)
            else:
                print(f"❌ OpenAI API error: {response.status_code}")
                return self._fallback_template(prompt)
        
        except Exception as e:
            print(f"❌ OpenAI API failed: {e}")
            return self._fallback_template(prompt)
    
    def _clean_code(self, code: str) -> str:
        """Remove markdown formatting from AI response"""
        
        # Remove code fences
        for fence in ["```hcl", "```terraform", "```"]:
            if fence in code:
                code = code.split(fence)[1]
                if "```" in code:
                    code = code.split("```")[0]
                break
        
        return code.strip()
    
    def _fallback_template(self, prompt: str) -> str:
        """Simple fallback template when AI unavailable"""
        
        date = datetime.now().strftime('%Y-%m-%d')
        
        # Detect what type of infrastructure from prompt
        prompt_lower = prompt.lower()
        
        if "vpc" in prompt_lower or "network" in prompt_lower:
            return f'''terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = "us-east-1"
}}

resource "aws_vpc" "main" {{
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {{
    Name        = "PromptInfra VPC"
    ManagedBy   = "promptinfra"
    CreatedAt   = "{date}"
    Environment = "development"
  }}
}}

resource "aws_subnet" "public" {{
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
  
  tags = {{
    Name        = "PromptInfra Public Subnet"
    ManagedBy   = "promptinfra"
    CreatedAt   = "{date}"
    Environment = "development"
  }}
}}'''
        
        # Default: EC2 instance
        return f'''terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = "us-east-1"
}}

resource "aws_instance" "main" {{
  ami           = "ami-0c02fb55956c7d316"  # Amazon Linux 2
  instance_type = "t2.micro"
  
  tags = {{
    Name        = "PromptInfra Instance"
    ManagedBy   = "promptinfra"
    CreatedAt   = "{date}"
    Environment = "development"
  }}
}}

output "instance_ip" {{
  value       = aws_instance.main.public_ip
  description = "Public IP of the instance"
}}'''
    
    def save_local(self, terraform_code: str):
        """Save Terraform code to local main.tf"""
        
        Path("main.tf").write_text(terraform_code)
        print("📁 Saved to main.tf")
    
    def push_to_terraform_cloud(self, terraform_code: str) -> bool:
        """Push Terraform code to Terraform Cloud workspace"""
        
        if not self.tf_token:
            print("⚠️  Skipping Terraform Cloud push (no API token)")
            return False
        
        print(f"☁️  Pushing to Terraform Cloud: {self.tf_org}/{self.tf_workspace}")
        
        try:
            # Create configuration version
            config_version_url = f"https://app.terraform.io/api/v2/workspaces/{self.tf_workspace}/configuration-versions"
            
            headers = {
                "Authorization": f"Bearer {self.tf_token}",
                "Content-Type": "application/vnd.api+json"
            }
            
            # Step 1: Create configuration version
            response = requests.post(
                config_version_url,
                headers=headers,
                json={
                    "data": {
                        "type": "configuration-versions",
                        "attributes": {
                            "auto-queue-runs": True,
                            "speculative": False
                        }
                    }
                },
                timeout=30
            )
            
            if response.status_code != 201:
                print(f"❌ Failed to create configuration version: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
            
            upload_url = response.json()["data"]["attributes"]["upload-url"]
            
            # Step 2: Upload Terraform code as tar.gz
            import tarfile
            import io
            
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
                # Add main.tf
                tf_data = terraform_code.encode('utf-8')
                tf_info = tarfile.TarInfo(name='main.tf')
                tf_info.size = len(tf_data)
                tar.addfile(tf_info, io.BytesIO(tf_data))
            
            tar_buffer.seek(0)
            
            upload_response = requests.put(
                upload_url,
                data=tar_buffer.read(),
                headers={"Content-Type": "application/octet-stream"},
                timeout=30
            )
            
            if upload_response.status_code == 200:
                print("✅ Successfully pushed to Terraform Cloud!")
                print(f"   View workspace: https://app.terraform.io/app/{self.tf_org}/workspaces/{self.tf_workspace}")
                return True
            else:
                print(f"❌ Upload failed: {upload_response.status_code}")
                return False
        
        except Exception as e:
            print(f"❌ Error pushing to Terraform Cloud: {e}")
            return False
    
    def run(self, prompt: str):
        """Main execution flow"""
        
        print("\n" + "="*60)
        print("🚀 PromptInfra - AI to Infrastructure")
        print("="*60)
        
        # Generate Terraform
        terraform_code = self.generate_terraform(prompt)
        
        # Save locally
        self.save_local(terraform_code)
        
        # Push to Terraform Cloud
        pushed = self.push_to_terraform_cloud(terraform_code)
        
        print("\n" + "="*60)
        print("✨ Generation Complete!")
        print("="*60)
        print(f"📝 Prompt: {prompt}")
        print(f"📁 Local: main.tf")
        print(f"☁️  Cloud: {'Pushed' if pushed else 'Local only'}")
        
        if pushed:
            print(f"\n🎯 Next: Review and apply in Terraform Cloud")
            print(f"   https://app.terraform.io/app/{self.tf_org}/workspaces/{self.tf_workspace}")
        else:
            print(f"\n🎯 Next: Apply locally")
            print(f"   terraform init")
            print(f"   terraform plan")
            print(f"   terraform apply")


def main():
    """CLI Entry Point"""
    
    if len(sys.argv) < 2:
        print("Usage: python promptinfra_minimal.py \"Your infrastructure prompt\"")
        print("\nExamples:")
        print("  python promptinfra_minimal.py \"Create an EC2 instance\"")
        print("  python promptinfra_minimal.py \"Set up a VPC with subnets\"")
        print("  python promptinfra_minimal.py \"Deploy a web server\"")
        sys.exit(1)
    
    prompt = " ".join(sys.argv[1:])
    
    try:
        infra = PromptInfra()
        infra.run(prompt)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
