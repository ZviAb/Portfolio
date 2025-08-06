variable "project_prefix" {
  type        = string
  description = "Prefix for naming all resources"
}

variable "resource_tags" {
  type        = map(string)
  description = "Common tags to apply to all resources"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where security groups will be created"
}

variable "admin_cidr_blocks" {
  type        = list(string)
  description = "CIDR blocks allowed to access EKS API server"
}

