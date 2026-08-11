variable "repository_name" {
  type = string
}

variable "image_tag_mutability" {
  description = "MUTABLE or IMMUTABLE"
  type        = string
  default     = "MUTABLE"
}

variable "scan_on_push" {
  type    = bool
  default = true
}

variable "max_image_count" {
  description = "Max images to retain — keep low, ECR free tier is only 500MB/month storage"
  type        = number
  default     = 5
}

variable "tags" {
  type    = map(string)
  default = {}
}
