# PromptInfra Minimal

**AI-powered Terraform generator in ~250 lines**

Convert natural language → Terraform → Deploy to AWS via Terraform Cloud

---

## ⚡ Quick Start (30 seconds)

```powershell
# 1. Install
pip install -r requirements-minimal.txt

# 2. Generate infrastructure  
python promptinfra_minimal.py "Create an EC2 instance"

# 3. Apply
terraform init
terraform plan
terraform apply
```

**That's it!** ✅

---

## 🔑 Configuration (Optional)

Works without configuration! But for full features:

```powershell
# Copy example
Copy-Item .env.example .env

# Edit with your keys
notepad .env
```

Add your keys to `.env`:
```bash
OPENAI_API_KEY=sk-...              # For AI generation (optional - has fallback)
TF_API_TOKEN=...                   # For Terraform Cloud (optional - works locally)
TF_ORGANIZATION=your-org           # Your TF Cloud org
TF_WORKSPACE=promptinfra-workspace # Your TF Cloud workspace
```

**Get API keys:**
- OpenAI: https://platform.openai.com/api-keys
- Terraform Cloud: https://app.terraform.io/app/settings/tokens

---

## 💡 Examples

```powershell
# Simple EC2
python promptinfra_minimal.py "Create a t2.micro instance"

# VPC
python promptinfra_minimal.py "Create a VPC with public subnet"

# Database
python promptinfra_minimal.py "Create an RDS database"

# Complex
python promptinfra_minimal.py "Create 3-tier web app with load balancer"
```

---

## 🎯 Features

- ✅ **AI-powered** - Natural language → Terraform
- ✅ **Works offline** - Fallback templates when no API
- ✅ **Smart caching** - Same prompt = instant results
- ✅ **Cloud integration** - Pushes to Terraform Cloud
- ✅ **Auto-tagging** - All resources tagged for cost tracking
- ✅ **Minimal** - 250 lines, 2 dependencies

---

## 🐛 Troubleshooting

**"No module named 'requests'"**
```powershell
pip install -r requirements-minimal.txt
```

**"OPENAI_API_KEY not set"**  
→ This is OK! Uses fallback templates. Or add your key to `.env`

**"TF_API_TOKEN not set"**  
→ This is OK! Generates local `main.tf`. Or add token for cloud push.

---

## 📁 Files

```
promptinfra_minimal.py       ← Main script (250 lines)
requirements-minimal.txt     ← Dependencies (2 packages)
.env.example                 ← Config template
main.tf                      ← Generated Terraform
cache/                       ← Cached generations
```

---

## 🏷️ Cost Tracking

All resources auto-tagged:
```hcl
tags = {
  ManagedBy   = "promptinfra"
  CreatedAt   = "2025-10-15"
  Environment = "development"
}
```

Track costs in:
- **Terraform Cloud**: Cost estimate per run
- **AWS Cost Explorer**: Filter by `ManagedBy = promptinfra`

---

## 🚀 How It Works

1. Takes your prompt
2. Checks cache (instant if found)
3. Generates Terraform (AI or fallback)
4. Saves to `main.tf`
5. Optionally pushes to Terraform Cloud
6. You review and apply

---

## 🔐 Security

- Add `.env` to `.gitignore` (don't commit API keys)
- Review generated Terraform before applying
- Use IAM roles with least privilege

---

## 💰 Cost

- **Free** with Terraform Cloud free tier
- **$0.002** per AI generation (OpenAI)
- **$0** using fallback templates

---

## 📖 For Technical Users

**Want to understand the implementation?** Read **`TECHNICAL.md`** for:
- Architecture diagrams
- Code structure breakdown
- Design patterns and decisions
- Extension points
- Performance characteristics

---

**Questions?** It's one file (~250 lines) - just read `promptinfra_minimal.py`!

**Start now:**
```powershell
python promptinfra_minimal.py "Create an EC2 instance"
```
