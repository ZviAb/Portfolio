variable "project_prefix" {
  type        = string
  description = "Prefix for naming all resources"
}

variable "resource_tags" {
  type        = map(string)
  description = "Common tags to apply to all resources"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "List of subnet IDs for the EKS worker nodes (using public subnets temporarily)"
}

variable "kubernetes_version" {
  type        = string
  description = "Kubernetes version for the EKS cluster"
  default     = "1.32"
}

variable "node_instance_types" {
  type        = list(string)
  description = "List of instance types for the node group"
  default     = ["t3a.medium"]
}

variable "capacity_type" {
  type        = string
  description = "Type of capacity associated with the EKS Node Group. Valid values: ON_DEMAND, SPOT"
  default     = "ON_DEMAND"
}

variable "ami_type" {
  type        = string
  description = "Type of Amazon Machine Image (AMI) associated with the EKS Node Group"
  default     = "AL2_x86_64"
}

variable "disk_size" {
  type        = number
  description = "Disk size in GiB for worker nodes"
  default     = 20
}

variable "desired_capacity" {
  type        = number
  description = "Desired number of worker nodes"
  default     = 2
}

variable "max_capacity" {
  type        = number
  description = "Maximum number of worker nodes"
  default     = 3
}

variable "min_capacity" {
  type        = number
  description = "Minimum number of worker nodes"
  default     = 1
}

variable "max_unavailable" {
  type        = number
  description = "Maximum number of nodes unavailable at once during a version update"
  default     = 1
}

variable "cluster_role_arn" {
  type        = string
  description = "ARN of the EKS cluster IAM role"
}

variable "node_group_role_arn" {
  type        = string
  description = "ARN of the EKS node group IAM role"
}

variable "cluster_security_group_id" {
  type        = string
  description = "Security group ID for the EKS cluster"
}

variable "nodes_security_group_id" {
  type        = string
  description = "Security group ID for the EKS worker nodes"
}

