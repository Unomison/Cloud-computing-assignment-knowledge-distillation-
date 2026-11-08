# Knowledge Distillation & Lightweight Command Parser on Local Cloud (CS3081)

**Student Name:** UTKARSH SINGH  
**Roll Number:** 230101079  
**GitHub Repository:** [https://github.com/Unomison/Cloud-computing-assignment-knowledge-distillation-](https://github.com/Unomison/Cloud-computing-assignment-knowledge-distillation-)  
**Latest Release Assets:** [GitHub Releases v1.0.0](https://github.com/Unomison/Cloud-computing-assignment-knowledge-distillation-/releases/tag/v1.0.0)  

---

## 1. Project Overview & Architecture

This repository contains the complete implementation of a cloud-native, sequence-level knowledge-distilled command-parsing language model deployed on a local Kubernetes cluster. 

The system distills a 3.8-billion parameter teacher model (**`phi3.5`** via Ollama) into a 70-million parameter student model (**`EleutherAI/pythia-70m`**), parsing natural language voice commands into an exact 4-key JSON schema (`intent`, `date`, `time`, `place`).

```
                    +------------------------------------+
                    |        Ollama (Phi-3.5)            |
                    |         (Teacher Model)            |
                    +-----------------+------------------+
                                      |
                     Parallel Sharded | Generation
                                      v
+------------------+       +----------+----------+       +------------------+
|  Worker Shard 0  | ----> |   datasets/teacher/ | <---- |  Worker Shard 1  |
+------------------+       +----------+----------+       +------------------+
                                      |
                                      v clean.py
                           +----------+----------+
                           |  datasets/v1/train  |
                           +----------+----------+
                                      |
                                      v make train
                           +----------+----------+
                           | Pythia-70M (Student)|
                           +----------+----------+
                                      |
                                      v Upload weights
                           +----------+----------+
                           |   SeaweedFS (S3)    |
                           +----------+----------+
                                      |
                                      v Startup download
                           +----------+----------+
                           | Kubernetes Cluster  |
                           |   (Namespace: app)  |
                           |  - Traefik Ingress  |
                           |  - HPA Autoscaler   |
                           |  - Inference Pods   |
                           +---------------------+
```

---

## 2. Directory Structure

```
├── .github/workflows/
│   └── ci.yml                   # 5-stage GitHub Actions CI/CD workflow
├── cluster/
│   ├── k3d.yaml                 # k3d cluster config (port 8080 & 8333 forwards)
│   └── seaweedfs.yaml           # SeaweedFS deployment in data namespace
├── data/
│   ├── commands_pool.jsonl      # 3,000 unlabelled training command pool
│   ├── validation.jsonl         # 100 gold labelled evaluation commands
│   ├── schema.json              # Output JSON schema specification
│   └── rate_card.json           # Hypothetical cloud billing rates
├── datasets/
│   ├── teacher/                 # Sharded teacher outputs (shard-0, shard-1)
│   └── v1/                      # Cleaned train.jsonl & train.sha256
├── manifests/
│   └── app.yaml                 # Namespace, Deployment, Service, Ingress, HPA
├── models/
│   ├── v1/                      # Trained student v1 weights & model.sha256
│   └── v2/                      # Trained student v2 weights & model.sha256
├── network/
│   ├── subnets.md               # 10.20.0.0/16 Subnet table & explanations
│   ├── nacl.json                # Public subnet stateless firewall rules
│   └── packets_sample.jsonl     # Sample packets for NACL verification
├── prompts/
│   └── teacher_prompt.txt       # Ollama Phi-3.5 prompt template
├── report/
│   ├── report.tex               # LaTeX source for mini project technical report
│   └── report.pdf               # Compiled 6-page comprehensive report (<= 8 pages)
├── results/
│   ├── teacher_validation.json  # Teacher evaluation report on validation.jsonl
│   ├── student_score.json       # Distilled student evaluation report
│   ├── loadtest_stats.csv       # Locust load test statistics (5,400 requests)
│   ├── loadtest_headers.json    # Replica and version header distribution
│   ├── cold_start.log           # Pod cold-start latency measurements (median: 4.0s)
│   ├── recovery.log             # Pod failure and recovery under load
│   └── memory_test.log          # 50-request sequential memory test under limits
├── service/
│   ├── app.py                   # Port 8000 microservice (/parse, /healthz, /readyz)
│   ├── Dockerfile               # Lean CPU-only container image (<= 2 GB)
│   └── requirements.txt         # Pinned dependency requirements
├── tests/
│   └── test_service.py          # Unit tests (Schema, extraction, NACL rules)
├── tools/
│   ├── score.py                 # Ground-truth scoring & quality gate evaluator
│   ├── nacl_sim.py              # Stateless NACL packet simulator
│   ├── locustfile.py            # Locust load test script
│   └── evaluate_models.py       # Validation evaluator across all 3 models
├── worker/
│   ├── worker.py                # Parallel labelling worker (SHARD_INDEX / COUNT)
│   ├── clean.py                 # Shard aggregator and rule (a)-(e) filter
│   ├── Dockerfile               # Worker container image
│   └── pipeline.yaml            # Pipeline namespace jobs
├── 230101079.pdf                # 3-Page Handwritten Reflection Notes
├── AI_USE.md                    # AI usage transparency statement
├── Makefile                     # System build, deploy, test, tear down targets
└── README.md                    # Main project documentation
```

---

## 3. Quick Start: Build, Deploy, Test, Tear Down

The entire workflow can be managed through the `Makefile`:

### 1. Build and Deploy Local Cloud (`make up`)
```bash
# In at most 3 commands:
k3d cluster create --config cluster/k3d.yaml
kubectl apply -f cluster/seaweedfs.yaml
kubectl apply -f manifests/app.yaml
```
*Alternatively, simply execute:*
```bash
make up
```

### 2. Run Automated Verification & Tests (`make test`)
```bash
make test
```
This automatically executes:
1. Unit tests across service schema parsing and NACL packet rules (`python -m unittest discover -s tests -p "test_*.py" -v`).
2. Score report evaluation against the quality gate:
   ```bash
   python tools/score.py results/student_predictions.jsonl data/validation.jsonl --min-validity 95
   ```
3. Stateless NACL simulation check:
   ```bash
   python tools/nacl_sim.py network/nacl.json network/packets_sample.jsonl --check
   ```

### 3. Model Training & Verification (`make train`)
```bash
# Quick verification run on first 50 records:
make train SUBSET=50

# Full training run using training/config.yaml:
make train
```

### 4. Locust Load Testing
```bash
pip install locust
locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 2m --host http://localhost:8080 --csv results/loadtest
```

### 5. Tear Down and Cleanup (`make down`)
```bash
make down
```

---

## 4. Key Results Summary

| Metric | Teacher (Phi-3.5) | Untrained Pythia-70M | Distilled Student (v1) | Target Threshold |
| :--- | :--- | :--- | :--- | :--- |
| **JSON Validity** | 100.0% | 0.0% | **99.0%** | $\ge 95.0\%$ |
| **Full-Frame Accuracy** | 100.0\% | 0.0\% | **96.0%** | $\ge 50.0\%$ |
| **Throughput (req/s)** | --- | --- | **45.0 req/s** | Sustained load |
| **p50 Latency** | --- | --- | **82 ms** | Normal load |
| **p95 Latency** | --- | --- | **135 ms** | $\le 5,000$ ms |
| **Error Rate** | --- | --- | **0.11%** (6 / 5,400) | $\le 1.0\%$ |
| **Container Size** | --- | --- | **1.04 GB** | $\le 2.0$ GB |
| **Peak Memory (RSS)** | --- | --- | **231.2 MiB** | $\le 1.0$ GiB limit |
| **Cold-Start Duration**| --- | --- | **4.0 s (median)** | 3 runs verified |

---

## 5. Cost & SLO Calculations

- **Hourly Cost of 2 Replicas:**
  $$\text{Hourly Cost} = 2 \times [(1.0 \times 3.50) + (1.0 \times 0.45)] = \mathbf{7.90 \text{ INR/hour}}$$
- **Cost per 1,000 Requests:**
  $$\text{Cost} = \frac{7.90 \text{ INR}}{162,000 \text{ req/hr}} \times 1000 = \mathbf{0.049 \text{ INR}}$$
- **SLO & Error Budget:**
  - Objective: 99.0% successful requests over a 2-minute load test (5,400 requests).
  - Error Budget: $5400 \times (1 - 0.99) = 54\text{ requests}$.
  - Budget Used: $6 / 54 = \mathbf{11.11\%}$ (88.89% remaining).

---

## 6. GitHub Repository & Releases

- **GitHub Repository:** [https://github.com/Unomison/Cloud-computing-assignment-knowledge-distillation-](https://github.com/Unomison/Cloud-computing-assignment-knowledge-distillation-)
- **CI/CD Quality Gate Demonstration:**
  - Passing CI Run: [Actions Run #1](https://github.com/Unomison/Cloud-computing-assignment-knowledge-distillation-/actions)
  - Gate Failure Demonstration (Untrained Pythia-70M): [Actions Run #2 (Failed at Quality Gate)](https://github.com/Unomison/Cloud-computing-assignment-knowledge-distillation-/actions)
- **Submission Commit Tag:** `final`
