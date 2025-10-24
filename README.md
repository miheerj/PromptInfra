# PromptInfra
**IaC at the speed of thought.**  
Turn plain English into Terraform code you can actually use.

---

### Why this exists
Terraform is amazing, but writing boilerplate and waiting for plans can be painful.  
I wanted something simple: **type what you want → get Terraform → apply it**.  
So I built PromptInfra with a little help from OpenAI and some caching magic.

---

### What it does
- Converts **natural language prompts** into `main.tf`
- Adds **smart caching** so repeated plans are faster
- Works with **Terraform Cloud/Enterprise** (optional)
- Falls back to templates if you don’t have an API key
- Tags resources for **cost tracking**

---

### Quick Start
```bash
# Install
pip install -r requirements-minimal.txt

# Generate Terraform
python promptinfra_minimal.py "Create an EC2 instance"

# Apply
terraform init
terraform plan
terraform apply

```

### Demo
(Add your GIF here from VS Code recording)
!PromptInfra demo

### How It Works
1. You type a prompt.
2. Checks cache (instant if seen before).
3. Generates Terraform using AI or fallback templates.
4. Saves to `main.tf` for you to review.
5. Apply locally or push to Terraform Cloud.


### Contribute
Ideas? Bugs? PRs welcome. Keep it simple and clear.
Open an issue or submit a pull request.

### License
MIT License.
README.md
Displaying README.md.

