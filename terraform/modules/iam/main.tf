# FinOps least-privilege IAM role + OIDC trust for GitHub Actions
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_role" "github_actions" {
  name = "${var.project}-github-actions"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Principal = {
          Federated = data.aws_iam_openid_connect_provider.github.arn
        }

        Action = "sts:AssumeRoleWithWebIdentity"

        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}@${var.github_owner_id}/${var.github_repo}@${var.github_repo_id}:*"
          }
        }
      }
    ]
  })

  tags = var.tags
}


resource "aws_iam_role_policy" "github_actions" {
  name = "${var.project}-github-actions-policy"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TerraformState"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.state_bucket}",
          "arn:aws:s3:::${var.state_bucket}/*"
        ]
      },
      {
        Sid    = "DeployFinOpsResources"
        Effect = "Allow"
        Action = [
          "iam:*",
          "s3:*",
          "budgets:*",
          "ce:*",
          "lambda:*",
          "ecs:*",
          "ecr:*",
          "logs:*",
          "events:*",
          "ssm:*",
          "secretsmanager:GetSecretValue",
          "ec2:*",
          "elasticloadbalancing:*",
          "ses:*",
          "sns:*",
          "cloudwatch:*",
          "application-autoscaling:*"
        ]
        Resource = "*"
      }
    ]
  })
}

# ── Runtime role for the FinOps application ─────────────────────────────────
resource "aws_iam_role" "finops_app" {
  name = "${var.project}-app"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = [
            "ecs-tasks.amazonaws.com",
            "lambda.amazonaws.com",
            "ec2.amazonaws.com"
          ]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "finops_app" {
  name = "${var.project}-app-policy"
  role = aws_iam_role.finops_app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CostExplorerRead"
        Effect = "Allow"
        Action = [
          "ce:GetCostAndUsage",
          "ce:GetCostForecast",
          "ce:GetDimensionValues",
          "ce:GetTags",
          "ce:GetAnomalies",
          "ce:GetAnomalyMonitors",
          "ce:GetAnomalySubscriptions"
        ]
        Resource = "*"
      },
      {
        Sid    = "BudgetsRead"
        Effect = "Allow"
        Action = [
          "budgets:ViewBudget",
          "budgets:DescribeBudgets",
          "budgets:DescribeBudget*"
        ]
        Resource = "*"
      },
      {
        Sid    = "SESSend"
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      },
      {
        Sid    = "S3Reports"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.reports_bucket}",
          "arn:aws:s3:::${var.reports_bucket}/*"
        ]
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Sid      = "STS"
        Effect   = "Allow"
        Action   = ["sts:GetCallerIdentity"]
        Resource = "*"
      }
    ]
  })
}

# ── ECS Task Execution Role ────────────────────────────────────────────────
# Used by ECS/Fargate to perform startup operations such as:
# - pulling the container image from ECR
# - sending container logs to CloudWatch
# - retrieving ECS secrets

resource "aws_iam_role" "ecs_execution" {
  name = "${var.project}-ecs-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }

        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "ecs_execution" {
  name = "${var.project}-ecs-execution-policy"
  role = aws_iam_role.ecs_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      [
        {
          Sid    = "ECRPull"
          Effect = "Allow"
          Action = [
            "ecr:GetAuthorizationToken",
            "ecr:BatchCheckLayerAvailability",
            "ecr:GetDownloadUrlForLayer",
            "ecr:BatchGetImage"
          ]
          Resource = "*"
        },
        {
          Sid    = "CloudWatchLogs"
          Effect = "Allow"
          Action = [
            "logs:CreateLogStream",
            "logs:PutLogEvents"
          ]
          Resource = "*"
        }
      ],
      var.slack_webhook_url != null ? [
        {
          Sid    = "ReadSSMSecrets"
          Effect = "Allow"
          Action = [
            "ssm:GetParameter",
            "ssm:GetParameters"
          ]
          Resource = aws_ssm_parameter.slack_webhook_url[0].arn
        },
        {
          Sid    = "DecryptSSMSecret"
          Effect = "Allow"
          Action = [
            "kms:Decrypt"
          ]
          Resource = data.aws_kms_alias.ssm[0].target_key_arn
        }
      ] : []
    )
  })
}

resource "aws_iam_instance_profile" "finops_app" {
  name = "${var.project}-app"
  role = aws_iam_role.finops_app.name
}

# ── Slack webhook — stored as SSM SecureString, readable only by finops_app ──
resource "aws_ssm_parameter" "slack_webhook_url" {
  count = var.slack_webhook_url != null ? 1 : 0

  name  = "/finops/${var.project}/slack_webhook_url"
  type  = "SecureString"
  value = var.slack_webhook_url
  tags  = var.tags
}

data "aws_kms_alias" "ssm" {
  count = var.slack_webhook_url != null ? 1 : 0
  name  = "alias/aws/ssm"
}

resource "aws_iam_role_policy" "read_slack_webhook" {
  count = var.slack_webhook_url != null ? 1 : 0
  name  = "${var.project}-read-slack-webhook"
  role  = aws_iam_role.finops_app.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ReadSlackWebhookParam"
        Effect   = "Allow"
        Action   = ["ssm:GetParameters", "ssm:GetParameter"]
        Resource = aws_ssm_parameter.slack_webhook_url[0].arn
      },
      {
        Sid      = "DecryptSlackWebhookParam"
        Effect   = "Allow"
        Action   = ["kms:Decrypt"]
        Resource = data.aws_kms_alias.ssm[0].target_key_arn
      }
    ]
  })
}