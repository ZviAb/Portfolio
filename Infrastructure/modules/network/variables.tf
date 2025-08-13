variable "vpc_cidr_block" {
  type        = string
  description = "CIDR block for the VPC"
}



variable "project_prefix" {
  type        = string
  description = "Prefix for naming all resources"
}

variable "resource_tags" {
  type        = map(string)
  description = "Common tags to apply to all resources"
}

variable "subnet_count" {
  type        = number
  description = "Number of subnets to create"
  default     = 2
}
