#!/usr/bin/env bash
set -euo pipefail
echo "==> Bootstrapping AWS FinOps"
cp -n .env.example .env || true
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
mkdir -p data/reports
echo "==> Done. Edit .env then run: make run  or  make docker-up"
