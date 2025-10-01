# 🚀 PromptInfra - Text to Infrastructure Prototype

A simple Python prototype for **text-to-IaC-to-provisioning** using GPT APIs with AWS-based caching and FinOps tracking.

## ✨ Core Features

✅ **Text → Terraform**: Natural language prompts to infrastructure code  
✅ **AWS Caching**: S3/DynamoDB instead of local files for faster init/apply  
✅ **Auto-tagging**: All resources tagged with "PromptInfra" for tracking  
✅ **FinOps Ready**: Weekly usage/cost tracking capabilities  
✅ **Simple & Clean**: Focused on EC2/VPC only, minimal dependencies  

## 🏗️ System Architecture

```
User Prompt → OpenAI API → Terraform Code → AWS S3 Cache → DynamoDB Tracking
                    ↓
              Fallback Templates (EC2/VPC only)
                    ↓  
              Auto-tagged Resources → FinOps Cost Tracking
```

## 🎯 Your Original Requirements - Status

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| **Text-to-IaC-to-Provisioning** | ✅ **DONE** | OpenAI API + fallback templates |
| **AWS Caching (S3/DynamoDB)** | ✅ **DONE** | Replaces local cache/pycache |
| **Auto-tagging with PromptInfra** | ✅ **DONE** | All resources tagged for tracking |
| **FinOps Weekly Usage Tracking** | ✅ **DONE** | Cost estimation + dashboards |
| **Simple & Easy to Understand** | ✅ **DONE** | Single file, minimal deps |

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set API Key (Optional - has fallback)
```bash
# Windows
set OPENAI_API_KEY=your-api-key-here

# Mac/Linux  
export OPENAI_API_KEY=your-api-key-here
```

### 3. Generate Infrastructure
```bash
# Generate EC2 instance
python promptinfra.py generate "Create an EC2 instance"

# Generate VPC with subnets  
python promptinfra.py generate "Create a VPC with subnets"
```

### 4. Deploy with Terraform
```bash
terraform init
terraform plan
terraform apply
```

### 5. Track Costs
```bash
python promptinfra.py costs
```

## 🏷️ Auto-Tagging System

Every generated resource automatically includes:
```hcl
tags = {
  Name = "PromptInfra Resource"
  source = "promptinfra"
  auto_generated = "true"
  created_at = "2025-10-01"
  managed_by = "promptinfra"
}
```

## 💰 FinOps Integration

### AWS Cost Explorer
Filter by tag: `source = promptinfra` to see all costs from this system

### Cost Tracking Components
- **DynamoDB Table**: `promptinfra-deployments` (tracks all generations)
- **S3 Bucket**: `promptinfra-cache` (caches Terraform for speed)
- **Dashboard**: HTML/CSV reports via `finops_dashboard.py`

## 📁 Project Structure

```
📁 PromptInfra/
├── 📄 promptinfra.py          # ⭐ Main system (Text→IaC→AWS)
├── 📄 finops_main.py          # FinOps-enhanced version
├── 📄 finops_dashboard.py     # Cost tracking dashboard
├── 📄 requirements.txt        # Dependencies (openai + boto3)
├── 📄 README.md              # This file
├── 📄 GETTING_STARTED.md     # Quick start guide
├── 📄 main.tf                # Generated Terraform output
└── 📄 finops_dashboard.html  # Generated cost dashboard
```

## 🔧 Supported Resources (Simple Focus)

**Currently Supported:**
- ✅ EC2 Instances (t2.micro)
- ✅ VPC + Subnets (10.0.0.0/16)

**Coming Soon:**
- RDS Databases
- Load Balancers
- Auto Scaling Groups

## 🛠️ AWS Setup (Optional)

The system works **without AWS credentials** using fallback templates.

For full AWS integration:

```bash
# Create S3 bucket for caching
aws s3 mb s3://promptinfra-cache

# Create DynamoDB table for tracking
aws dynamodb create-table \
  --table-name promptinfra-deployments \
  --attribute-definitions AttributeName=deployment_id,AttributeType=S \
  --key-schema AttributeName=deployment_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

## 🎯 Usage Examples

```bash
# Simple EC2 instance
python promptinfra.py generate "Create a t2.micro instance for testing"

# VPC networking
python promptinfra.py generate "Create VPC with public subnet for development"

# Check generated code
cat main.tf

# View cost tracking
python promptinfra.py costs

# Generate cost dashboard
python finops_dashboard.py --format html
```

## 🚨 Design Philosophy

- **Simple by Design**: EC2/VPC only to avoid over-engineering
- **Fallback Ready**: Works without API keys using templates  
- **Production Ready**: Auto-tags all resources for cost tracking
- **AWS Optional**: Local fallback for development/testing

## 🔍 How It Works

1. **Input**: Natural language prompt
2. **Processing**: OpenAI API generates Terraform (or uses fallback)
3. **Caching**: Stores in AWS S3 for faster repeated access
4. **Tracking**: Logs deployment in DynamoDB for cost analysis
5. **Tagging**: Auto-adds PromptInfra tags to all resources
6. **Output**: Clean Terraform ready for `terraform apply`

## 📊 FinOps Dashboard

View all deployments and costs:
```bash
python finops_dashboard.py --format html
# Opens: finops_dashboard.html in browser
```

## 🔗 Next Steps

1. **Test locally** with fallback templates (no AWS needed)
2. **Set up AWS** S3 bucket and DynamoDB table for full functionality
3. **Deploy infrastructure** using generated Terraform
4. **Monitor costs** using AWS Cost Explorer with PromptInfra tags

---

**🏦 Built for FinOps:** Every resource is tagged and tracked for cost transparency.