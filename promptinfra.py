#!/usr/bin/env python3
"""
PromptInfra - Simple Text to Infrastructure with AWS-based Caching
Requirements:
1. Text → IaC → Infrastructure provisioning
2. AWS-based caching (S3/DynamoDB) instead of local files
3. Auto-tagging with PromptInfra for tracking
4. FinOps weekly usage tracking
"""

import os
import sys
import hashlib
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class PromptInfra:
    def __init__(self):
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        # AWS resource names (configurable via environment variables)
        self.s3_bucket = os.getenv('PROMPTINFRA_S3_BUCKET', 'promptinfra-cache')
        self.dynamodb_table = os.getenv('PROMPTINFRA_DYNAMODB_TABLE', 'promptinfra-deployments')
        
        # AWS clients (optional - will work without AWS credentials for testing)
        self.s3_client = None
        self.dynamodb_client = None
        
        self._setup_aws_clients()
    
    def _setup_aws_clients(self):
        """Setup AWS clients for caching"""
        try:
            import boto3
            self.s3_client = boto3.client('s3', region_name=self.aws_region)
            self.dynamodb_client = boto3.client('dynamodb', region_name=self.aws_region)
            logger.info("✅ AWS clients initialized for cloud caching")
        except ImportError:
            logger.warning("⚠️  boto3 not installed - using local fallback")
        except Exception as e:
            logger.warning(f"⚠️  AWS credentials not configured - using local fallback: {e}")
    
    def hash_prompt(self, prompt: str) -> str:
        """Generate hash for caching"""
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]
    
    def get_cached_terraform_aws(self, prompt_hash: str) -> str:
        """Get cached Terraform from AWS S3"""
        if not self.s3_client:
            return None
        
        try:
            bucket_name = self.s3_bucket
            key = f"terraform/{prompt_hash}.tf"
            
            response = self.s3_client.get_object(Bucket=bucket_name, Key=key)
            terraform_code = response['Body'].read().decode('utf-8')
            
            logger.info(f"📥 Retrieved from S3 cache: {prompt_hash}")
            return terraform_code
            
        except Exception as e:
            logger.debug(f"No S3 cache found for {prompt_hash}: {e}")
            return None
    
    def save_terraform_to_aws_cache(self, prompt_hash: str, terraform_code: str):
        """Save Terraform to AWS S3 cache"""
        if not self.s3_client:
            return
        
        try:
            bucket_name = self.s3_bucket
            key = f"terraform/{prompt_hash}.tf"
            
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=terraform_code,
                ContentType='text/plain',
                Metadata={
                    'cached_at': datetime.now().isoformat(),
                    'source': 'promptinfra'
                }
            )
            
            logger.info(f"📤 Saved to S3 cache: {prompt_hash}")
            
        except Exception as e:
            logger.warning(f"Failed to cache to S3: {e}")
    
    def track_deployment_aws(self, prompt_hash: str, prompt: str, terraform_code: str):
        """Track deployment in DynamoDB for FinOps"""
        if not self.dynamodb_client:
            return
        
        try:
            table_name = self.dynamodb_table
            
            # Count resources for cost estimation
            resource_count = terraform_code.count('resource "')
            
            self.dynamodb_client.put_item(
                TableName=table_name,
                Item={
                    'deployment_id': {'S': prompt_hash},
                    'created_at': {'S': datetime.now().isoformat()},
                    'prompt': {'S': prompt},
                    'resource_count': {'N': str(resource_count)},
                    'terraform_hash': {'S': hashlib.sha256(terraform_code.encode()).hexdigest()},
                    'status': {'S': 'generated'},
                    'tags': {'M': {
                        'source': {'S': 'promptinfra'},
                        'auto_generated': {'S': 'true'}
                    }}
                }
            )
            
            logger.info(f"📊 Tracked deployment in DynamoDB: {prompt_hash}")
            
        except Exception as e:
            logger.warning(f"Failed to track in DynamoDB: {e}")
    
    def generate_terraform_with_ai(self, prompt: str) -> str:
        """Generate Terraform using AI with PromptInfra tagging"""
        if not self.openai_key:
            return None
        
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.openai_key)
            
            system_prompt = """You are a Terraform expert. Generate AWS infrastructure code.

CRITICAL REQUIREMENTS:
1. Add these tags to ALL resources:
   - source = "promptinfra"
   - auto_generated = "true" 
   - created_at = current date
   - managed_by = "promptinfra"

2. Return ONLY Terraform code, no explanations
3. Use AWS provider version ~> 5.0
4. Follow Terraform best practices

Example tag structure:
tags = {
  Name = "resource-name"
  source = "promptinfra"
  auto_generated = "true"
  created_at = "2025-10-01"
  managed_by = "promptinfra"
}"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate Terraform for: {prompt}"}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            terraform_code = response.choices[0].message.content.strip()
            
            # Clean up response
            if "```" in terraform_code:
                start = terraform_code.find("```") + 3
                if terraform_code[start:start+3] in ["hcl", "ter"]:
                    start += 3
                end = terraform_code.find("```", start)
                terraform_code = terraform_code[start:end] if end != -1 else terraform_code[start:]
            
            return terraform_code.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None
    
    def generate_simple_fallback(self, prompt: str) -> str:
        """Simple fallback when AI is not available - EC2 and VPC only"""
        
        # Extract basic info from prompt
        if "vpc" in prompt.lower() or "network" in prompt.lower() or "subnet" in prompt.lower():
            return f'''terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = "{self.aws_region}"
}}

resource "aws_vpc" "promptinfra_vpc" {{
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {{
    Name = "PromptInfra VPC"
    source = "promptinfra"
    auto_generated = "true"
    created_at = "{datetime.now().strftime('%Y-%m-%d')}"
    managed_by = "promptinfra"
  }}
}}

resource "aws_subnet" "promptinfra_subnet" {{
  vpc_id     = aws_vpc.promptinfra_vpc.id
  cidr_block = "10.0.1.0/24"
  
  tags = {{
    Name = "PromptInfra Subnet"
    source = "promptinfra"
    auto_generated = "true"
    created_at = "{datetime.now().strftime('%Y-%m-%d')}"
    managed_by = "promptinfra"
  }}
}}

output "vpc_id" {{
  value = aws_vpc.promptinfra_vpc.id
}}'''
        
        # Default fallback - simple EC2 instance
        return f'''terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = "{self.aws_region}"
}}

resource "aws_instance" "promptinfra_instance" {{
  ami           = "ami-0c02fb55956c7d316"
  instance_type = "t2.micro"
  
  tags = {{
    Name = "PromptInfra Instance"
    source = "promptinfra"
    auto_generated = "true"
    created_at = "{datetime.now().strftime('%Y-%m-%d')}"
    managed_by = "promptinfra"
  }}
}}

output "instance_ip" {{
  value = aws_instance.promptinfra_instance.public_ip
}}'''
    
    def process_prompt(self, prompt: str) -> dict:
        """Main processing function"""
        logger.info(f"🚀 Processing: {prompt}")
        
        # Generate hash for caching
        prompt_hash = self.hash_prompt(prompt)
        logger.info(f"🔑 Hash: {prompt_hash}")
        
        # Try AWS cache first
        terraform_code = self.get_cached_terraform_aws(prompt_hash)
        
        if terraform_code:
            logger.info("✅ Using AWS cached result")
        else:
            # Generate new Terraform
            logger.info("🤖 Generating new Terraform...")
            terraform_code = self.generate_terraform_with_ai(prompt)
            
            if not terraform_code:
                logger.info("🔄 Using simple fallback...")
                terraform_code = self.generate_simple_fallback(prompt)
            
            if not terraform_code:
                return {'success': False, 'error': 'Failed to generate Terraform'}
            
            # Cache in AWS
            self.save_terraform_to_aws_cache(prompt_hash, terraform_code)
        
        # Track for FinOps
        self.track_deployment_aws(prompt_hash, prompt, terraform_code)
        
        # Save locally
        with open('main.tf', 'w') as f:
            f.write(terraform_code)
        
        return {
            'success': True,
            'terraform_code': terraform_code,
            'hash': prompt_hash,
            'cached': terraform_code is not None
        }

class FinOpsWeeklyTracker:
    """Simple weekly cost tracking using AWS services"""
    
    def __init__(self):
        self.dynamodb_table = os.getenv('PROMPTINFRA_DYNAMODB_TABLE', 'promptinfra-deployments')
        self.dynamodb_client = None
        try:
            import boto3
            self.dynamodb_client = boto3.client('dynamodb')
        except:
            pass
    
    def get_promptinfra_costs(self):
        """Get costs for all PromptInfra resources"""
        if not self.dynamodb_client:
            print("⚠️  DynamoDB not available for cost tracking")
            return
        
        try:
            # Get all deployments
            response = self.dynamodb_client.scan(
                TableName=self.dynamodb_table,
                FilterExpression='#src = :source',
                ExpressionAttributeNames={'#src': 'source'},
                ExpressionAttributeValues={':source': {'S': 'promptinfra'}}
            )
            
            deployments = response.get('Items', [])
            
            print(f"📊 Found {len(deployments)} PromptInfra deployments")
            
            total_resources = 0
            for deployment in deployments:
                resource_count = int(deployment.get('resource_count', {}).get('N', 0))
                total_resources += resource_count
                
                deployment_id = deployment.get('deployment_id', {}).get('S', 'unknown')
                created_at = deployment.get('created_at', {}).get('S', 'unknown')
                prompt = deployment.get('prompt', {}).get('S', 'unknown')
                
                print(f"  🆔 {deployment_id} - {resource_count} resources - {created_at[:10]}")
                print(f"     📝 {prompt[:60]}...")
            
            print(f"📊 Total PromptInfra resources: {total_resources}")
            print("💡 Use AWS Cost Explorer with tag filter: source=promptinfra")
            
        except Exception as e:
            print(f"❌ Error tracking costs: {e}")

def main():
    """Main CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PromptInfra - Text to Infrastructure")
    parser.add_argument("command", choices=['generate', 'costs'], help="Command to run")
    parser.add_argument("prompt", nargs='?', help="Infrastructure prompt")
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        if not args.prompt:
            print("❌ Please provide a prompt")
            sys.exit(1)
        
        infra = PromptInfra()
        result = infra.process_prompt(args.prompt)
        
        if result['success']:
            print("\\n" + "="*60)
            print("🏗️  PROMPTINFRA TERRAFORM GENERATED")
            print("="*60)
            print(f"🔑 Hash: {result['hash']}")
            print(f"💾 Cached: {'Yes' if result['cached'] else 'No'}")
            print(f"🏷️  Auto-tagged with PromptInfra identifiers")
            print(f"📁 Saved to: main.tf")
            print("="*60)
            print("\\n🎯 Next steps:")
            print("  terraform init")
            print("  terraform plan") 
            print("  terraform apply")
            print("\\n📊 Cost tracking:")
            print("  python promptinfra.py costs")
        else:
            print(f"❌ {result['error']}")
    
    elif args.command == 'costs':
        tracker = FinOpsWeeklyTracker()
        tracker.get_promptinfra_costs()

if __name__ == "__main__":
    main()
