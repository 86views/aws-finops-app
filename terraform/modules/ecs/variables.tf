variable "project_name" {
  type = string
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "container_image" {
  description = "Full ECR image URI including tag"
  type        = string
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "cpu" {
  description = "Fargate task CPU units — 256 (.25 vCPU) is the smallest/cheapest option"
  type        = number
  default     = 256
}

variable "memory" {
  description = "Fargate task memory (MB) — 512 pairs with cpu=256"
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "Number of running tasks — kept at 1 for free-tier usage"
  type        = number
  default     = 1
}

variable "execution_role_arn" {
  description = "ECS task execution role ARN (from existing iam module)"
  type        = string
}

variable "task_role_arn" {
  description = "ECS task role ARN the app assumes at runtime (from existing iam module)"
  type        = string
}

variable "subnet_ids" {
  description = "Public subnets — no NAT, so tasks need assign_public_ip = true"
  type        = list(string)
}

variable "security_group_ids" {
  type = list(string)
}

variable "target_group_arn" {
  type = string
}

variable "log_group_name" {
  type = string
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "environment_variables" {
  description = "Plain (non-secret) env vars for the container"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Map of container env var name => ARN in Secrets Manager/SSM"
  type        = map(string)
  default     = {}
}

variable "tags" {
  type    = map(string)
  default = {}
}
