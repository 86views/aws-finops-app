variable "bucket_name" {
  type        = string
  description = "Name of the S3 bucket for reports"
}

variable "retention_days" {
  type        = number
  default     = 90
  description = "Days after which reports are expired"
}

variable "tags" {
  type    = map(string)
  default = {}
}
