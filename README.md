# AWS FinOps Platform

**Automated FinOps tool to monitor, analyze, and optimize AWS spending.**

Ingests AWS billing data via Cost Explorer, detects anomalies, generates scheduled reports (PDF / HTML / CSV), and delivers insights via Slack, Email (SES), and a FastAPI web dashboard. Fully containerized with Docker and provisioned via Terraform.

## Architecture

```
GitHub → GitHub Actions (OIDC) → Terraform → AWS Account
                                              ├── Cost Explorer
                                              ├── Budgets
                                              └── Cost Anomaly Detection
                                                        │
                                                        ▼
                                              Dockerized Python App
                                              ├── SQLite (local analytics)
                                              ├── HTML / PDF / CSV reports
                                              ├── Slack + SES alerts
                                              └── FastAPI Dashboard
```

## Core Stack

| Layer | Technologies |
|-------|--------------|
| **Application** | Python 3.12, Boto3, Pandas, SQLite, FastAPI, WeasyPrint, Jinja2, Slack SDK |
| **Infrastructure** | Terraform, AWS S3, IAM, Lambda (optional scheduler), Budgets, Cost Anomaly Detection |
| **DevOps & Security** | Docker, GitHub Actions + OIDC, Trivy, Checkov, ruff, mypy |
| **Reporting & Dashboard** | FastAPI + interactive charts (Chart.js), tag breakdowns, MoM trends, forecasting |

## Key Features

- **Daily / Weekly cost reports** (PDF, HTML, CSV) broken down by service, account, tag, and region
- **Month-over-Month trends** and simple forecasting
- **AWS Cost Anomaly Detection** + **Budgets** integration with Slack / SES notifications
- **FastAPI dashboard** with interactive charts and tag-level cost visibility
- **Least-privilege IAM** roles via Terraform
- **OIDC-based CI/CD** (no long-lived AWS keys)
- **Security scanning** (Trivy on images, Checkov on Terraform)
- **Containerized** and ready for ECS / Fargate or local Docker Compose

## Quick Start

### Prerequisites

- AWS account with Cost Explorer enabled
- Terraform >= 1.9
- Docker / Docker Compose
- Python 3.12+
- GitHub repository (for OIDC)

### 1. Clone & Configure

```bash
cp .env.example .env
# Edit .env with your Slack webhook, SES identity, etc.
```

### 2. Provision Infrastructure

```bash
cd terraform/environments/dev
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply
```

### 3. Run Locally (Docker Compose)

```bash
docker compose up --build
```

- Dashboard: http://localhost:8000
- API docs: http://localhost:8000/docs

### 4. Generate a Report Manually

```bash
docker compose exec app python -m app.reports.cli --period daily
```

## Project Layout

```
aws-finops/
├── app/                    # Python application
│   ├── api/                # FastAPI routes
│   ├── core/               # Config, AWS clients, cost logic
│   ├── reports/            # PDF / HTML / CSV generation
│   ├── alerts/             # Slack + SES
│   ├── dashboard/          # Templates + static assets
│   ├── db/                 # SQLite models & migrations
│   └── utils/
├── terraform/              # Modular IaC
│   ├── modules/
│   └── environments/dev/
├── github/.github/workflows/
├── scripts/
├── tests/
├── docs/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## CI/CD

- **Lint & type-check** (ruff + mypy)
- **Unit / integration tests**
- **Checkov** on Terraform
- **Trivy** on Docker image
- **OIDC** deploy to AWS (no static credentials)

## Security Notes (2026 best practices)

- OIDC federation only (GitHub → AWS)
- Least-privilege IAM policies
- No secrets in code; use AWS Secrets Manager / SSM or GitHub Secrets
- Image scanning + IaC policy-as-code
- Read-only Cost Explorer / Budgets permissions where possible

## License

MIT
