# 🚀 PromptInfra - Quick Setup

**Minimal AI-to-Infrastructure prototype in ~250 lines**

## ✨ What This Does

```
Natural Language → AI → Terraform Code → Terraform Cloud → AWS Infrastructure
```

Example: `"Create an EC2 instance"` → Generates Terraform → Pushes to TF Cloud → You review & apply

---

## 📋 Prerequisites

1. **Python 3.7+** installed
2. **OpenAI API Key** (optional - has fallback templates)
3. **Terraform Cloud Account** (free tier works)

---

## 🛠️ Installation (2 minutes)

### Step 1: Install Dependencies

```powershell
pip install -r requirements-minimal.txt
```

### Step 2: Configure API Keys

Create a `.env` file:

```powershell
# Copy the example
Copy-Item .env.example .env

# Edit .env with your keys
notepad .env
```

Fill in:
```bash
OPENAI_API_KEY=sk-your-key-here
TF_API_TOKEN=your-tf-cloud-token
TF_ORGANIZATION=your-org-name
TF_WORKSPACE=promptinfra-workspace
```

### Step 3: Load Environment Variables

```powershell
# Load .env variables
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}
```

---

## 🎯 Usage

### Basic Usage

```powershell
python promptinfra_minimal.py "Create an EC2 instance for development"
```

### More Examples

```powershell
# Simple EC2
python promptinfra_minimal.py "Create a t2.micro instance"

# VPC networking
python promptinfra_minimal.py "Set up a VPC with public subnet"

# Web server
python promptinfra_minimal.py "Deploy a web server with security group"

# Database
python promptinfra_minimal.py "Create an RDS database for testing"
```

---

## 🔑 Getting API Keys

### OpenAI API Key (Optional)
1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy and save in `.env`

**Note:** Without this, the tool uses fallback templates (still works!)

### Terraform Cloud Token (For Cloud Push)
1. Go to https://app.terraform.io/app/settings/tokens
2. Click "Create an API token"
3. Copy and save in `.env`

**Note:** Without this, the tool only generates local `main.tf` files

### Terraform Cloud Workspace Setup
1. Go to https://app.terraform.io
2. Create organization (if needed)
3. Create workspace named `promptinfra-workspace` (or custom name)
4. Connect to your cloud provider (AWS/Azure/GCP)

---

## 📁 What Gets Created

```
cache/              ← Cached Terraform code (prevents regeneration)
  abc123def456.tf   ← Cached by prompt hash

main.tf             ← Generated Terraform code (ready to apply)

.env                ← Your API keys (DO NOT COMMIT)
```

---

## 🎬 Workflow

1. **You run**: `python promptinfra_minimal.py "Create an EC2 instance"`

2. **Script does**:
   - Checks cache (skip AI if already generated)
   - Calls OpenAI API to generate Terraform
   - Saves to `main.tf` locally
   - Pushes to Terraform Cloud workspace
   - Displays workspace URL

3. **You review in Terraform Cloud**:
   - View the plan
   - Check cost estimate
   - Click "Confirm & Apply"

4. **Infrastructure deployed** ✅

---

## 🏷️ Auto-Tagging

All resources automatically tagged:
```hcl
tags = {
  Name        = "Descriptive Name"
  ManagedBy   = "promptinfra"
  CreatedAt   = "2025-10-14"
  Environment = "development"
}
```

Use these tags in AWS Cost Explorer to track spending!

---

## ⚡ Quick Commands

```powershell
# Generate only (no cloud push)
$env:TF_API_TOKEN=""; python promptinfra_minimal.py "Create VPC"

# View cached Terraform
Get-ChildItem cache/*.tf | Select-Object -First 1 | Get-Content

# Clear cache
Remove-Item cache/*.tf

# Test without OpenAI (uses fallback)
$env:OPENAI_API_KEY=""; python promptinfra_minimal.py "Create EC2"
```

---

## 🔧 Troubleshooting

### "No module named 'requests'"
```powershell
pip install -r requirements-minimal.txt
```

### "OPENAI_API_KEY not set"
- **This is OK!** The tool will use fallback templates
- Or add your key to `.env`

### "TF_API_TOKEN not set"
- **This is OK!** Code saves to `main.tf` locally
- Apply manually: `terraform init && terraform plan && terraform apply`

### Push to Terraform Cloud fails
- Verify token: https://app.terraform.io/app/settings/tokens
- Verify workspace name matches `.env`
- Check organization name is correct

---

## 📊 Cost Tracking

### In Terraform Cloud:
- Every run shows **cost estimate** before applying
- Track historical costs per workspace
- Set up budget alerts

### In AWS Cost Explorer:
- Filter by tag: `ManagedBy = promptinfra`
- View all resources created by this tool
- Set up cost anomaly detection

---

## 🎯 What's Different from Full Codebase?

**This minimal version** (~250 lines):
- ✅ AI prompt to Terraform generation
- ✅ Terraform Cloud integration
- ✅ Simple caching
- ✅ Fallback templates
- ✅ Auto-tagging

**Removed complexity**:
- ❌ S3/DynamoDB caching (TF Cloud handles this)
- ❌ Custom Lambda cost monitoring (TF Cloud has cost estimates)
- ❌ JSON deployment tracking (TF Cloud has run history)
- ❌ Multiple file variants
- ❌ Complex orchestration

**Result:** Simple, focused, production-ready prototype

---

## 🚀 Next Steps

1. **Test locally** first (generates `main.tf`)
2. **Review generated code** before pushing
3. **Set up Terraform Cloud** for automatic cost tracking
4. **Deploy infrastructure** with confidence

---

## 💡 Pro Tips

- **Cache is your friend**: Same prompt = instant results
- **Review before apply**: Always check the generated code
- **Use TF Cloud cost estimates**: See costs before deploying
- **Tag everything**: Makes cost tracking easy
- **Start small**: Test with simple prompts first

---

**Need help?** Check the generated `main.tf` or Terraform Cloud workspace for details.
