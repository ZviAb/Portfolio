variable "project_prefix" {
  type        = string
  description = "Prefix for naming all resources"
}

variable "resource_tags" {
  type        = map(string)
  description = "Common tags to apply to all resources"
}

variable "cluster_name" {
  type        = string
  description = "Name of the EKS cluster"
}

variable "cluster_oidc_issuer_url" {
  type        = string
  description = "OIDC issuer URL for the EKS cluster"
}