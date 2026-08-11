# Architecture

## Overview

The AWS FinOps platform is a containerised Python application that:

1. Pulls cost data from **AWS Cost Explorer**
2. Persists lightweight snapshots in **SQLite**
3. Generates **CSV / HTML / PDF** reports on a schedule
4. Sends **Slack + SES** notifications for summaries and anomalies
5. Exposes a **FastAPI** dashboard and REST API
6. Is provisioned by **Terraform** (S3, IAM, Budgets, Anomaly Detection)
7. Is delivered via **GitHub Actions + OIDC** (no long-lived keys)

## Data Flow

```
Cost Explorer ──► Python app (Boto3 + Pandas)
                      │
                      ├── SQLite snapshots
                      ├── Report engine (Jinja2 + WeasyPrint)
                      ├── Slack webhook / SES
                      └── FastAPI (JSON + HTML dashboard)
```

## Security Model (2026)

| Concern | Approach |
|---------|----------|
| CI credentials | GitHub OIDC → IAM role (no access keys) |
| Runtime permissions | Dedicated least-privilege IAM role for Cost Explorer, Budgets, SES, S3 |
| Secrets | `.env` locally; AWS Secrets Manager / SSM or GitHub Secrets in prod |
| Image | Multi-stage, non-root user, Trivy scan in CI |
| IaC | Checkov policy-as-code on every PR |
| Network | Dashboard intended behind ALB / API Gateway + auth in production |

## Scheduling

APScheduler runs inside the container:

- Daily report + anomaly check (default 08:00 UTC)
- Weekly report (default Monday 09:00 UTC)

For production at scale prefer EventBridge + Lambda or ECS scheduled tasks.

## Extension Points

- Add more Cost Explorer dimensions / tags
- Persist snapshots to DynamoDB / Timestream instead of SQLite
- Integrate AWS Compute Optimizer recommendations
- Multi-account via AWS Organizations / CUR
