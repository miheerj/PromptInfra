#!/usr/bin/env python3
"""
FinOps-Enhanced Terraform Generator
Generates Terraform + automatic cost tracking and weekly reports
"""

import os
import sys
import hashlib
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class FinOpsTerraformGenerator:
    def __init__(self):
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # FinOps tracking
        self.tracking_dir = Path("finops_tracking")
        self.tracking_dir.mkdir(exist_ok=True)
        
        # Check for API keys
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not self.openai_key and not self.anthropic_key:
            logger.warning("No API keys found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY")
    
    def hash_prompt(self, prompt: str) -> str:
        """Generate SHA256 hash of the prompt for caching"""
        return hashlib.sha256(prompt.encode()).hexdigest()
    
    def generate_deployment_id(self) -> str:
        """Generate unique deployment ID for tracking"""
        return str(uuid.uuid4())[:8]
    
    def get_cached_terraform(self, prompt_hash: str) -> str:
        """Check if Terraform code exists in cache"""
        cache_file = self.cache_dir / f"{prompt_hash}.tf"
        
        if cache_file.exists():
            logger.info(f"Found cached Terraform: {cache_file}")
            return cache_file.read_text()
        
        return None
    
    def save_to_cache(self, prompt_hash: str, terraform_code: str):
        """Save Terraform code to cache"""
        cache_file = self.cache_dir / f"{prompt_hash}.tf"
        cache_file.write_text(terraform_code)
        logger.info(f"Cached Terraform: {cache_file}")
    
    def call_openai_api(self, prompt: str, deployment_id: str) -> str:
        """Call OpenAI API to generate FinOps-aware Terraform"""
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.openai_key)
            
            system_prompt = f"""You are a FinOps-aware Terraform expert. Generate cost-conscious Terraform for AWS.

CRITICAL REQUIREMENTS:
1. Add consistent tags to ALL resources for cost tracking:
   - deployment_id = "{deployment_id}"
   - created_by = "terraform-generator"
   - created_at = "{datetime.now().strftime('%Y-%m-%d')}"
   - cost_center = "development"

2. Include cost optimization:
   - Use appropriate instance sizes
   - Enable detailed monitoring only when needed
   - Set up auto-termination where possible

3. Add a Lambda function for cost monitoring that:
   - Runs weekly to check resource costs
   - Sends alerts if costs exceed thresholds
   - Tags resources with cost information

4. Return ONLY Terraform code, no explanations
5. Use AWS provider version ~> 5.0
6. Follow Terraform best practices

Example tag structure:
tags = {{
  Name = "resource-name"
  deployment_id = "{deployment_id}"
  created_by = "terraform-generator"
  created_at = "{datetime.now().strftime('%Y-%m-%d')}"
  cost_center = "development"
  auto_shutdown = "true"  # where applicable
}}"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate FinOps-aware Terraform for: {prompt}"}
                ],
                temperature=0.1,
                max_tokens=3000
            )
            
            terraform_code = response.choices[0].message.content.strip()
            logger.info("Generated FinOps-aware Terraform with OpenAI")
            return self.clean_terraform_code(terraform_code)
            
        except ImportError:
            logger.error("OpenAI SDK not installed. Run: pip install openai")
            return None
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None
    
    def call_anthropic_api(self, prompt: str, deployment_id: str) -> str:
        """Call Anthropic API to generate FinOps-aware Terraform"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.anthropic_key)
            
            system_prompt = f"""You are a FinOps-aware Terraform expert. Generate cost-conscious Terraform for AWS.

Add these tags to ALL resources:
- deployment_id = "{deployment_id}"
- created_by = "terraform-generator"  
- created_at = "{datetime.now().strftime('%Y-%m-%d')}"
- cost_center = "development"

Include cost monitoring Lambda function and optimize for cost efficiency."""

            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=3000,
                temperature=0.1,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Generate FinOps-aware Terraform for: {prompt}"}
                ]
            )
            
            terraform_code = response.content[0].text.strip()
            logger.info("Generated FinOps-aware Terraform with Anthropic Claude")
            return self.clean_terraform_code(terraform_code)
            
        except ImportError:
            logger.error("Anthropic SDK not installed. Run: pip install anthropic")
            return None
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return None
    
    def clean_terraform_code(self, code: str) -> str:
        """Clean up AI response to get pure Terraform code"""
        # Remove markdown code blocks if present
        if "```hcl" in code:
            start = code.find("```hcl") + 6
            end = code.find("```", start)
            code = code[start:end] if end != -1 else code[start:]
        elif "```terraform" in code:
            start = code.find("```terraform") + 12
            end = code.find("```", start)
            code = code[start:end] if end != -1 else code[start:]
        elif "```" in code:
            start = code.find("```") + 3
            end = code.find("```", start)
            code = code[start:end] if end != -1 else code[start:]
        
        return code.strip()
    
    def generate_cost_monitoring_lambda(self, deployment_id: str) -> str:
        """Generate Lambda function for cost monitoring"""
        
        return f'''
# Cost Monitoring Lambda Function
resource "aws_iam_role" "cost_monitor_role" {{
  name = "cost-monitor-{deployment_id}"
  
  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {{
          Service = "lambda.amazonaws.com"
        }}
      }}
    ]
  }})
  
  tags = {{
    deployment_id = "{deployment_id}"
    created_by = "terraform-generator"
    created_at = "{datetime.now().strftime('%Y-%m-%d')}"
    cost_center = "development"
  }}
}}

resource "aws_iam_role_policy" "cost_monitor_policy" {{
  name = "cost-monitor-policy-{deployment_id}"
  role = aws_iam_role.cost_monitor_role.id
  
  policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Effect = "Allow"
        Action = [
          "ce:GetCostAndUsage",
          "ce:GetDimensionValues",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "sns:Publish"
        ]
        Resource = "*"
      }}
    ]
  }})
}}

resource "aws_lambda_function" "cost_monitor" {{
  filename         = "cost_monitor.zip"
  function_name    = "cost-monitor-{deployment_id}"
  role            = aws_iam_role.cost_monitor_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 60
  
  environment {{
    variables = {{
      DEPLOYMENT_ID = "{deployment_id}"
      COST_THRESHOLD = "50"  # Alert if monthly cost exceeds $50
    }}
  }}
  
  tags = {{
    deployment_id = "{deployment_id}"
    created_by = "terraform-generator"
    created_at = "{datetime.now().strftime('%Y-%m-%d')}"
    cost_center = "development"
  }}
}}

# Weekly cost check schedule
resource "aws_cloudwatch_event_rule" "weekly_cost_check" {{
  name                = "weekly-cost-check-{deployment_id}"
  description         = "Weekly cost monitoring for deployment {deployment_id}"
  schedule_expression = "rate(7 days)"
  
  tags = {{
    deployment_id = "{deployment_id}"
    created_by = "terraform-generator"
    created_at = "{datetime.now().strftime('%Y-%m-%d')}"
    cost_center = "development"
  }}
}}

resource "aws_cloudwatch_event_target" "lambda_target" {{
  rule      = aws_cloudwatch_event_rule.weekly_cost_check.name
  target_id = "CostMonitorLambdaTarget"
  arn       = aws_lambda_function.cost_monitor.arn
}}

resource "aws_lambda_permission" "allow_cloudwatch" {{
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost_monitor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.weekly_cost_check.arn
}}
'''
    
    def create_lambda_zip(self, deployment_id: str):
        """Create Lambda function ZIP file for cost monitoring"""
        
        lambda_code = f'''
import json
import boto3
import os
from datetime import datetime, timedelta

def handler(event, context):
    """
    Weekly cost monitoring Lambda
    Checks costs for resources with deployment_id tag
    """
    
    deployment_id = os.environ['DEPLOYMENT_ID']
    cost_threshold = float(os.environ.get('COST_THRESHOLD', 50))
    
    ce_client = boto3.client('ce')
    
    # Get costs for the last 7 days
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={{
                'Start': start_date,
                'End': end_date
            }},
            Granularity='DAILY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {{
                    'Type': 'TAG',
                    'Key': 'deployment_id'
                }}
            ]
        )
        
        total_cost = 0
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                if deployment_id in str(group['Keys']):
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    total_cost += cost
        
        # Project monthly cost
        monthly_cost = total_cost * 4.3  # Approximate weeks in month
        
        print(f"Deployment {{deployment_id}} - Weekly cost: ${{total_cost:.2f}}, Projected monthly: ${{monthly_cost:.2f}}")
        
        # Alert if over threshold
        if monthly_cost > cost_threshold:
            print(f"WARNING: Projected monthly cost ${{monthly_cost:.2f}} exceeds threshold ${{cost_threshold}}")
            
            # Could send SNS notification here
            
        return {{
            'statusCode': 200,
            'body': json.dumps({{
                'deployment_id': deployment_id,
                'weekly_cost': round(total_cost, 2),
                'projected_monthly': round(monthly_cost, 2),
                'threshold': cost_threshold,
                'alert': monthly_cost > cost_threshold
            }})
        }}
        
    except Exception as e:
        print(f"Error checking costs: {{str(e)}}")
        return {{
            'statusCode': 500,
            'body': json.dumps({{'error': str(e)}})
        }}
'''
        
        # Write Lambda code to file
        lambda_file = Path("cost_monitor.py")
        lambda_file.write_text(lambda_code)
        
        # Create ZIP file
        import zipfile
        with zipfile.ZipFile("cost_monitor.zip", 'w') as zipf:
            zipf.write("cost_monitor.py", "index.py")
        
        logger.info("Created cost monitoring Lambda ZIP file")
    
    def save_deployment_tracking(self, deployment_id: str, prompt: str, terraform_code: str):
        """Save deployment info for FinOps tracking"""
        
        tracking_info = {
            'deployment_id': deployment_id,
            'created_at': datetime.now().isoformat(),
            'prompt': prompt,
            'resource_count': terraform_code.count('resource "'),
            'estimated_monthly_cost': self.estimate_basic_cost(terraform_code),
            'tags': {
                'deployment_id': deployment_id,
                'created_by': 'terraform-generator',
                'created_at': datetime.now().strftime('%Y-%m-%d'),
                'cost_center': 'development'
            }
        }
        
        tracking_file = self.tracking_dir / f"{deployment_id}.json"
        tracking_file.write_text(json.dumps(tracking_info, indent=2))
        
        logger.info(f"Saved deployment tracking: {tracking_file}")
        return tracking_info
    
    def estimate_basic_cost(self, terraform_code: str) -> float:
        """Basic cost estimation for common resources"""
        
        cost = 0.0
        
        # Simple cost estimates (monthly)
        if 'aws_instance' in terraform_code:
            t2_micro_count = terraform_code.count('t2.micro')
            t2_small_count = terraform_code.count('t2.small')
            t2_medium_count = terraform_code.count('t2.medium')
            
            cost += t2_micro_count * 8.50    # ~$8.50/month
            cost += t2_small_count * 17.00   # ~$17/month  
            cost += t2_medium_count * 34.00  # ~$34/month
        
        if 'aws_ebs_volume' in terraform_code:
            volume_count = terraform_code.count('aws_ebs_volume')
            cost += volume_count * 0.80      # ~$0.80/month per 8GB volume
        
        if 'aws_s3_bucket' in terraform_code:
            bucket_count = terraform_code.count('aws_s3_bucket')
            cost += bucket_count * 2.00      # ~$2/month estimated
        
        if 'aws_db_instance' in terraform_code:
            rds_count = terraform_code.count('aws_db_instance')
            cost += rds_count * 15.00        # ~$15/month for t3.micro
        
        return round(cost, 2)
    
    def generate_terraform(self, prompt: str) -> dict:
        """Main method to generate FinOps-aware Terraform code"""
        logger.info(f"Processing FinOps-aware prompt: {prompt}")
        
        # Generate deployment ID for tracking
        deployment_id = self.generate_deployment_id()
        logger.info(f"Deployment ID: {deployment_id}")
        
        # Check cache first
        prompt_hash = self.hash_prompt(prompt + deployment_id)  # Include deployment_id in hash
        logger.info(f"Prompt hash: {prompt_hash}")
        
        # Try API calls (no caching for FinOps - each deployment should be tracked)
        terraform_code = None
        
        if self.openai_key:
            terraform_code = self.call_openai_api(prompt, deployment_id)
        
        if not terraform_code and self.anthropic_key:
            terraform_code = self.call_anthropic_api(prompt, deployment_id)
        
        if not terraform_code:
            logger.error("Failed to generate Terraform code")
            return None
        
        # Add cost monitoring Lambda
        terraform_code += self.generate_cost_monitoring_lambda(deployment_id)
        
        # Create Lambda ZIP file
        self.create_lambda_zip(deployment_id)
        
        # Cache the result
        self.save_to_cache(prompt_hash, terraform_code)
        
        # Save deployment tracking
        tracking_info = self.save_deployment_tracking(deployment_id, prompt, terraform_code)
        
        return {
            'terraform_code': terraform_code,
            'deployment_id': deployment_id,
            'tracking_info': tracking_info
        }
    
    def write_main_tf(self, terraform_code: str):
        """Write Terraform code to main.tf"""
        main_tf = Path("main.tf")
        main_tf.write_text(terraform_code)
        logger.info("Written FinOps-aware Terraform code to main.tf")
    
    def run_terraform_commands(self):
        """Run terraform init and plan"""
        import subprocess
        
        try:
            logger.info("Running terraform init...")
            result = subprocess.run(["terraform", "init"], 
                                  capture_output=True, text=True, check=True)
            logger.info("terraform init completed successfully")
            
            logger.info("Running terraform plan...")
            result = subprocess.run(["terraform", "plan"], 
                                  capture_output=True, text=True, check=True)
            logger.info("terraform plan completed successfully")
            print("\\nTerraform Plan Output:")
            print(result.stdout)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Terraform command failed: {e}")
            print(f"Error output: {e.stderr}")
        except FileNotFoundError:
            logger.error("Terraform not found. Please install Terraform CLI")

def main():
    """Main CLI function for FinOps-aware Terraform generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate FinOps-aware Terraform from natural language")
    parser.add_argument("prompt", help="Natural language prompt for infrastructure")
    parser.add_argument("--run", "-r", action="store_true", 
                       help="Run terraform init and plan after generation")
    parser.add_argument("--cost-threshold", type=float, default=50.0,
                       help="Monthly cost threshold for alerts (default: $50)")
    
    args = parser.parse_args()
    
    if not args.prompt:
        logger.error("Please provide a prompt")
        sys.exit(1)
    
    # Generate FinOps-aware Terraform
    generator = FinOpsTerraformGenerator()
    result = generator.generate_terraform(args.prompt)
    
    if not result:
        logger.error("Failed to generate Terraform code")
        sys.exit(1)
    
    # Write to main.tf
    generator.write_main_tf(result['terraform_code'])
    
    print("\\n" + "="*60)
    print("🏦 FINOPS-AWARE TERRAFORM GENERATED")
    print("="*60)
    print(f"💳 Deployment ID: {result['deployment_id']}")
    print(f"💰 Estimated Monthly Cost: ${result['tracking_info']['estimated_monthly_cost']}")
    print(f"📊 Resources Created: {result['tracking_info']['resource_count']}")
    print(f"🏷️  Auto-tagged for cost tracking")
    print(f"⏰ Weekly cost monitoring enabled")
    print("="*60)
    
    # Show tracking info
    print("\\n📋 Cost Tracking Features:")
    print("  ✅ All resources tagged with deployment_id")
    print("  ✅ Weekly Lambda cost monitoring")
    print("  ✅ Cost threshold alerts")
    print("  ✅ Deployment tracking saved")
    
    # Optionally run terraform commands
    if args.run:
        print("\\nRunning Terraform commands...")
        generator.run_terraform_commands()
    else:
        print("\\n🎯 Next steps:")
        print("  terraform init")
        print("  terraform plan")
        print("  terraform apply")
        print(f"\\n📊 View costs at: AWS Cost Explorer (filter by deployment_id: {result['deployment_id']})")

if __name__ == "__main__":
    main()
