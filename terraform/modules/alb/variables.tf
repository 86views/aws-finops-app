variable "project_name" {
  type = string
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  description = "ALB must sit in at least two public subnets across AZs"
  type        = list(string)
}

variable "alb_security_group_id" {
  type = string
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "health_check_path" {
  type    = string
  default = "/health"
}

variable "deregistration_delay" {
  description = "Seconds — kept low since this is a single-task (desired_count=1) free-tier setup"
  type        = number
  default     = 30
}

variable "tags" {
  type    = map(string)
  default = {}
}
