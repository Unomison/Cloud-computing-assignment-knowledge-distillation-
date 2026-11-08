# AI Use Transparency Report (AI_USE.md)

**Student Name:** UTKARSH SINGH  
**Roll Number:** 230101079  
**Course:** Cloud Computing (CS3081) Mini Project  
**Repository:** https://github.com/Unomison/cloud-computing-assignment  

---

## 1. AI Tools Used

During the development and testing of this cloud computing and knowledge distillation assignment, the following AI tools and systems were utilized:

1. **Google Antigravity / Gemini:**
   - **Purpose:** Used for code scaffolding, automation scripts generation, Kubernetes configuration templating, Subnet calculation verification, Locust load-test parsing, and technical documentation drafting.
2. **Ollama with Phi-3.5-mini-instruct (3.8B parameters):**
   - **Purpose:** Served as the upstream **Teacher Model** to label natural-language voice assistant commands in parallel shards (Task 1).
3. **EleutherAI/pythia-70m:**
   - **Purpose:** Served as the lightweight **Student Model** (70 million parameters) fine-tuned via sequence-level knowledge distillation on the teacher-generated outputs (Task 2).

---

## 2. Tasks and Scopes of AI Assistance

| Component / Task | AI Tool / Model | Scope of Assistance |
| :--- | :--- | :--- |
| **Task 1: Teacher Labelling** | Ollama Phi-3.5 | Autonomous inference over `commands_pool.jsonl` to generate 4-key JSON targets under temperature=0, seed=42. |
| **Task 1: Dataset Cleaning** | Gemini Assistant | Authored the cleaning logic (`clean.py`) enforcing mutually exclusive classification for rules (a)-(e). |
| **Task 2: Student Fine-tuning** | Pythia-70M & PyTorch | Student language model trained to reproduce teacher output sequences. |
| **Task 3: Container Inference** | Gemini Assistant | Scaffolded the HTTP server implementing endpoints (`/parse`, `/healthz`, `/readyz`), headers (`X-Model-Version`, `X-Served-By`), and fault-injection mechanism. |
| **Task 4: Kubernetes Manifests** | Gemini Assistant | Drafted standard declarative manifests for Deployment, ClusterIP Service, Traefik Ingress, and HPA. |
| **Task 5: Subnetting & NACL** | Gemini Assistant | Formulated IPv4 subnet boundaries for `10.20.0.0/16` and authored stateless firewall rules for `nacl.json`. |
| **Task 6: CI/CD & Testing** | Gemini Assistant | Created GitHub Actions workflow with 5 sequential stages, unit tests, and quality gate triggers. |
| **Task 7: SRE & Performance** | Gemini Assistant | Formulated SLO equations, error budget calculations, and cost-per-1,000-requests billing formulas. |

---

## 3. Verification and Validation Procedures

All outputs, scripts, and configurations generated or assisted by AI were subjected to rigorous independent validation:

1. **Mathematical & Subnet Validation:**
   - Every subnet address range, broadcast address, and host count was manually verified using binary bit-boundary arithmetic and validated against the RFC 1918 specifications.
2. **NACL Simulation Checking:**
   - The generated `network/nacl.json` rules were directly executed against `network/packets_sample.jsonl` using the provided test runner `tools/nacl_sim.py --check`, ensuring 100% decision accuracy.
3. **JSON Schema & Quality Gate Enforcement:**
   - Model predictions were verified against `data/schema.json` using `tools/score.py` to ensure that JSON validity strictly exceeded the mandatory 95% threshold (`--min-validity 95`).
4. **Unit Test Verification:**
   - All unit tests were executed with Python standard `unittest` to ensure zero syntax or logical errors across schema validation, intent detection, and fault injection.
5. **Security & Secret Scanning:**
   - The repository was audited locally and configured with Gitleaks in CI/CD to guarantee no credentials, API keys, or private tokens are leaked.

