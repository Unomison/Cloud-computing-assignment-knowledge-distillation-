# Makefile for Cloud Computing Mini Project (CS3081)
# Student: UTKARSH SINGH (230101079)

PYTHON ?= python
K3D ?= k3d
KUBECTL ?= kubectl
DOCKER ?= docker

.PHONY: all up down train test lint clean

all: test

# Task 2: Training commands
train:
	$(PYTHON) training/train.py $(if $(SUBSET),--subset $(SUBSET),)

# Task 6: System lifecycle commands
up:
	@echo "Creating k3d cluster..."
	$(K3D) cluster create --config cluster/k3d.yaml || true
	@echo "Deploying SeaweedFS in data namespace..."
	$(KUBECTL) apply -f cluster/seaweedfs.yaml
	@echo "Deploying Inference Service in app namespace..."
	$(KUBECTL) apply -f manifests/app.yaml
	@echo "System deployed successfully. Ingress accessible at http://localhost:8080"

down:
	@echo "Deleting cluster..."
	$(K3D) cluster delete cloud-cluster || true

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py" -v
	$(PYTHON) tools/score.py results/student_predictions.jsonl data/validation.jsonl --min-validity 95
	$(PYTHON) tools/nacl_sim.py network/nacl.json network/packets_sample.jsonl --check

lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=.git,__pycache__,extracted

clean:
	rm -rf __pycache__ tests/__pycache__ service/__pycache__ tools/__pycache__

