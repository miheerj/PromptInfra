# Technical Architecture & Scope

**For: Technical reviewers, contributors, and developers**

---

## 🎯 Project Scope

**What this is:**
- Minimal proof-of-concept: Natural language → Terraform code generator
- Single-file implementation (~250 lines)
- Designed for prototyping and learning

**What this is NOT:**
- Production-grade enterprise solution
- Multi-cloud orchestration platform
- Complex infrastructure management system

---

## 🏗️ Architecture

### High-Level Flow

```
┌─────────────┐
│ User Prompt │ "Create an EC2 instance"
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│   promptinfra_minimal.py            │
│   ┌──────────────────────────────┐  │
│   │ 1. Hash prompt (SHA-256)     │  │
│   │    → cache key: abc123...    │  │
│   └──────┬───────────────────────┘  │
│          │                           │
│          ▼                           │
│   ┌──────────────────────────────┐  │
│   │ 2. Check cache/abc123.tf     │  │
│   │    ├─ Hit  → Return cached   │  │
│   │    └─ Miss → Generate new    │  │
│   └──────┬───────────────────────┘  │
│          │                           │
│          ▼                           │
│   ┌──────────────────────────────┐  │
│   │ 3. Generation Strategy:      │  │
│   │    ├─ Try OpenAI API         │  │
│   │    └─ Fallback to template   │  │
│   └──────┬───────────────────────┘  │
│          │                           │
│          ▼                           │
│   ┌──────────────────────────────┐  │
│   │ 4. Clean & validate output   │  │
│   │    - Remove markdown fences  │  │
│   │    - Inject auto-tags        │  │
│   └──────┬───────────────────────┘  │
│          │                           │
│          ▼                           │
│   ┌──────────────────────────────┐  │
│   │ 5. Write outputs:            │  │
│   │    ├─ cache/abc123.tf        │  │
│   │    ├─ main.tf                │  │
│   │    └─ TF Cloud (optional)    │  │
│   └──────────────────────────────┘  │
└─────────────────────────────────────┘
       │
       ├────────────────┬───────────────┐
       ▼                ▼               ▼
┌────────────┐  ┌─────────────┐  ┌──────────────┐
│ Local File │  │ Local Cache │  │ TF Cloud API │
│  main.tf   │  │  cache/*.tf │  │  (optional)  │
└────────────┘  └─────────────┘  └──────────────┘
```

---

## 📂 File Structure

```
promptinfra_minimal.py    # Single implementation file
├── Class: PromptInfra
│   ├── __init__()                        # Setup: API keys, paths
│   ├── generate_terraform(prompt)        # Main orchestration
│   ├── _call_openai(prompt)             # OpenAI API integration
│   ├── _fallback_template(prompt)       # Offline templates
│   ├── _clean_code(code)                # Remove markdown
│   ├── save_local(code)                 # Write main.tf
│   ├── push_to_terraform_cloud(code)    # TF Cloud API
│   └── run(prompt)                      # End-to-end flow
└── main()                               # CLI entry point

requirements-minimal.txt  # Dependencies
├── requests              # HTTP client (OpenAI API, TF Cloud API)
└── python-dotenv         # Environment variable loader

.env.example             # Configuration template
├── OPENAI_API_KEY       # Optional: AI generation
├── TF_API_TOKEN         # Optional: TF Cloud push
├── TF_ORGANIZATION      # TF Cloud org name
└── TF_WORKSPACE         # TF Cloud workspace name

README.md                # User-facing documentation
TECHNICAL.md             # This file - technical details
.gitignore               # Version control exclusions
```

---

## 🔧 Core Components

### 1. Cache Manager (Lines ~30-60)
```python
def generate_terraform(prompt: str) -> str:
    # SHA-256 hash for deterministic cache keys
    cache_key = hashlib.sha256(prompt.encode()).hexdigest()[:12]
    cache_file = self.cache_dir / f"{cache_key}.tf"
    
    # Check cache first (O(1) file lookup)
    if cache_file.exists():
        return cache_file.read_text()
    
    # Cache miss - generate new
    # ...
```

**Design decisions:**
- **SHA-256 truncated to 12 chars** - Balance between collision resistance and readability
- **File-based cache** - Simple, no external dependencies (Redis/Memcached)
- **No TTL/expiration** - Cache is permanent (can be manually cleared)

### 2. AI Generator (Lines ~80-130)
```python
def _call_openai(prompt: str) -> str:
    # System prompt constrains output to valid Terraform
    system_prompt = """You are a Terraform expert..."""
    
    # OpenAI Chat Completions API
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {self.openai_key}"},
        json={
            "model": "gpt-3.5-turbo",    # Cost-optimized model
            "temperature": 0.1,           # Low variance for infrastructure
            "max_tokens": 2000            # ~500 lines of Terraform
        }
    )
```

**Design decisions:**
- **gpt-3.5-turbo** - $0.002/1K tokens (cheap for prototyping)
- **temperature=0.1** - Deterministic output for infrastructure code
- **System prompt engineering** - Constrains output to valid HCL syntax

### 3. Fallback Templates (Lines ~140-220)
```python
def _fallback_template(prompt: str) -> str:
    # Keyword detection (simple NLP)
    if "vpc" in prompt.lower():
        return VPC_TEMPLATE
    else:
        return EC2_TEMPLATE  # Default
```

**Design decisions:**
- **Simple keyword matching** - No ML/NLP libraries needed
- **Hardcoded templates** - Fast, reliable, works offline
- **Two templates** - EC2 (default) and VPC (most common)

### 4. Terraform Cloud Integration (Lines ~225-280)
```python
def push_to_terraform_cloud(code: str) -> bool:
    # Step 1: Create configuration version
    config_version = requests.post(
        f"{TF_CLOUD_API}/workspaces/{workspace}/configuration-versions"
    )
    
    # Step 2: Package as tar.gz
    tar_buffer = create_tarfile({"main.tf": code})
    
    # Step 3: Upload to presigned URL
    requests.put(upload_url, data=tar_buffer)
```

**Design decisions:**
- **Tar.gz format** - TF Cloud API requirement
- **Auto-queue runs** - Immediate feedback in UI
- **Graceful degradation** - Falls back to local file if no token

---

## 🔌 External Dependencies

### OpenAI API
- **Endpoint:** `https://api.openai.com/v1/chat/completions`
- **Model:** `gpt-3.5-turbo`
- **Cost:** ~$0.002 per generation
- **Fallback:** Local templates if unavailable

### Terraform Cloud API
- **Endpoint:** `https://app.terraform.io/api/v2/`
- **Authentication:** Bearer token
- **Actions:** Create config version, upload tar.gz
- **Fallback:** Local main.tf generation

---

## 🎯 Design Patterns

### 1. **Fail-Safe Pattern**
```python
# Every external call has a fallback
if self.openai_key:
    code = self._call_openai(prompt)
else:
    code = self._fallback_template(prompt)

if not code:  # API failed
    code = self._fallback_template(prompt)
```

### 2. **Cache-Aside Pattern**
```python
# Read-through cache
cached = get_from_cache(key)
if cached:
    return cached

generated = expensive_operation()
save_to_cache(key, generated)
return generated
```

### 3. **Template Method Pattern**
```python
def run(prompt):
    code = self.generate_terraform(prompt)  # Orchestration
    self.save_local(code)                   # Step 1
    self.push_to_terraform_cloud(code)      # Step 2 (optional)
```

---

## 🔐 Security Considerations

### Input Validation
```python
# Prompt is text-only (no code execution)
# Passed to AI API as string parameter
# No eval(), exec(), or subprocess with user input
```

### API Key Management
```python
# Keys loaded from environment variables
# Never logged or printed
# Not included in generated Terraform
```

### Generated Code Review
```python
# Always review main.tf before applying
# User controls terraform apply
# No automatic infrastructure provisioning
```

---

## 📊 Performance Characteristics

| Operation | Time | Cost | Cacheable |
|-----------|------|------|-----------|
| Cache hit | <100ms | $0 | N/A |
| OpenAI API call | ~5-10s | $0.002 | Yes |
| Fallback template | <10ms | $0 | Yes |
| TF Cloud upload | ~2-3s | $0 | No |

**Bottlenecks:**
- OpenAI API latency (network + generation time)
- Terraform Cloud upload (network + processing)

**Optimizations:**
- Cache hits eliminate AI calls entirely
- Fallback templates are instant
- Single-file architecture minimizes I/O

---

## 🧪 Testing Strategy

### Manual Testing
```powershell
# Test 1: No API keys (fallback mode)
$env:OPENAI_API_KEY=""; python promptinfra_minimal.py "Create EC2"

# Test 2: Cache hit
python promptinfra_minimal.py "Create EC2"  # First run
python promptinfra_minimal.py "Create EC2"  # Second run (should be instant)

# Test 3: TF Cloud integration
$env:TF_API_TOKEN="..."; python promptinfra_minimal.py "Create VPC"

# Test 4: Generated code validation
terraform init && terraform validate
```

### Unit Tests (Not Included - Minimal Prototype)
```python
# If you want to add tests:
# test_cache_key_generation()
# test_openai_fallback()
# test_template_selection()
# test_terraform_cloud_upload()
```

---

## 🚀 Extension Points

### Adding New Templates
```python
# In _fallback_template():
if "rds" in prompt.lower() or "database" in prompt.lower():
    return RDS_TEMPLATE
elif "lambda" in prompt.lower():
    return LAMBDA_TEMPLATE
```

### Adding More LLM Providers
```python
def _call_anthropic(prompt: str) -> str:
    # Similar structure to _call_openai()
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": self.anthropic_key},
        json={"model": "claude-3-haiku-20240307", ...}
    )
```

### Adding Validation
```python
def _validate_terraform(code: str) -> bool:
    # Run terraform validate
    result = subprocess.run(
        ["terraform", "validate", "-json"],
        capture_output=True
    )
    return result.returncode == 0
```

---

## 📈 Scalability

### Current Limits
- **Concurrent users:** 1 (single-file, local cache)
- **Cache size:** Unlimited (file-based)
- **Prompt length:** 2000 tokens (~500 words)
- **Generated code:** 2000 tokens (~500 lines Terraform)

### Scaling Options
1. **Multi-user:**
   - Shared cache → Redis/Memcached
   - User isolation → Workspace per user

2. **Distributed:**
   - Cache → S3/DynamoDB (original design had this)
   - API → Serverless function (Lambda/Cloud Run)

3. **Enterprise:**
   - Multiple LLM providers (fallback chain)
   - Custom validation rules (OPA/Sentinel)
   - Terraform module generation
   - Multi-cloud support (AWS/Azure/GCP)

---

## 🔄 Why This Design?

### Single File
- **Pro:** Easy to understand, deploy, and modify
- **Con:** Less modular than multi-file architecture
- **Decision:** Prioritize simplicity for prototype

### Local Cache
- **Pro:** No external dependencies, works offline
- **Con:** Not shared across users/machines
- **Decision:** Sufficient for single-user prototyping

### Minimal Dependencies
- **Pro:** Fast install, small attack surface
- **Con:** Limited functionality vs full frameworks
- **Decision:** 2 packages cover all needs (HTTP + env)

### No Testing Framework
- **Pro:** Reduced complexity for prototype
- **Con:** No automated validation
- **Decision:** Manual testing sufficient for PoC

---

## 🎓 Learning Path

**Understanding this codebase:**
1. Read `main()` function (entry point)
2. Trace `run()` method (orchestration)
3. Study `generate_terraform()` (core logic)
4. Explore `_call_openai()` and `_fallback_template()` (alternatives)
5. Optional: `push_to_terraform_cloud()` (cloud integration)

**Total reading time:** ~30 minutes

---

## 🔗 Related Technologies

- **Terraform:** Infrastructure as Code
- **OpenAI API:** GPT-3.5/4 for code generation
- **Terraform Cloud:** State management, cost estimation
- **AWS:** Target cloud platform (easily extensible)

---

## 📝 Notes for Contributors

### Code Style
- **PEP 8 compliant** (Python style guide)
- **Type hints:** Not used (minimal prototype)
- **Docstrings:** Function-level only

### Adding Features
1. Keep single-file architecture
2. Maintain fallback strategies
3. Test without external dependencies first
4. Document in README.md

### Performance
- Optimize for cache hits (most common case)
- Network calls are acceptable (user-triggered)
- Don't over-optimize (premature optimization)

---

## 🐛 Known Limitations

1. **Single cloud:** AWS only (templates are AWS-specific)
2. **Simple templates:** Only EC2 and VPC fallbacks
3. **No validation:** Generated code not validated before writing
4. **English only:** Prompts assumed to be English
5. **No state management:** Each run is independent
6. **Basic error handling:** Fails gracefully but minimal retry logic

---

## 📊 Metrics

**Lines of Code:** ~250  
**Dependencies:** 2  
**Functions:** 7  
**External APIs:** 2 (optional)  
**Supported Resources:** All AWS (via AI), EC2+VPC (fallback)  

**Cyclomatic Complexity:** Low (minimal branching)  
**Maintainability Index:** High (single file, clear flow)  

---

**Questions?** Read the code - it's only 250 lines! 🚀
