variable "project_name" {
  type = string
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "vpc_id" {
  description = "VPC to create security groups in"
  type        = string
}

variable "container_port" {
  description = "Port the FastAPI app listens on inside the container"
  type        = number
  default     = 8000
}

variable "alb_ingress_cidrs" {
  description = "CIDRs allowed to hit the ALB (default: open to internet on 80)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "enable_https" {
  description = "Whether to open 443 on the ALB security group"
  type        = bool
  default     = false
}

variable "tags" {
  type    = map(string)
  default = {}
}
