# =============================================================================
# AWS CONFIGURATION
# =============================================================================

variable "aws_region" {
  type        = string
  description = "AWS region for resources"
  default     = "ap-south-1"
}

# =============================================================================
# NETWORK CONFIGURATION
# =============================================================================

variable "vpc_cidr_block" {
  type        = string
  description = "CIDR block for the VPC"
  default     = "10.0.0.0/16"
}

variable "subnet_count" {
  type        = number
  description = "Number of subnets to create"
  default     = 2
}

# =============================================================================
# PROJECT CONFIGURATION
# =============================================================================

variable "project_prefix" {
  type        = string
  description = "Prefix for naming all resources"
}

variable "resource_tags" {
  type        = map(string)
  description = "Common tags to apply to all resources"
  default = {
    Project         = "QuizApp"
    ManagedBy       = "terraform"
    owner           = "zvi.abramovich"
    bootcamp        = "BC25"
    expiration_date = "05-08-25"
  }
}

# =============================================================================
# EKS CLUSTER CONFIGURATION
# =============================================================================

variable "kubernetes_version" {
  type        = string
  description = "Kubernetes version for the EKS cluster"
  default     = "1.32"
}

# =============================================================================
# EKS NODE GROUP CONFIGURATION
# =============================================================================

variable "node_instance_types" {
  type        = list(string)
  description = "List of instance types for the EKS node group"
  default     = ["t3a.medium"]
}

variable "capacity_type" {
  type        = string
  description = "Type of capacity associated with the EKS Node Group (ON_DEMAND or SPOT)"
  default     = "ON_DEMAND"
}

variable "desired_capacity" {
  type        = number
  description = "Desired number of worker nodes"
  default     = 3
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

# =============================================================================
# ARGOCD CONFIGURATION
# =============================================================================

# Git Repository Configuration
variable "git_repo_url" {
  type        = string
  description = "Git repository URL for ArgoCD applications (SSH format)"
}

variable "aws_secrets_name" {
  type        = string
  description = "AWS Secrets Manager secret name containing SSH keys and ArgoCD password"
}

# Infrastructure Applications Configuration
variable "infra_app_name" {
  type        = string
  description = "Name for infrastructure ArgoCD application (app-of-apps pattern)"
  default     = "infra-apps"
}

variable "infra_path" {
  type        = string
  description = "Path for infrastructure applications in git repository"
  default     = "infra-apps"
}

# Quiz Application Configuration
variable "quiz_app_name" {
  type        = string
  description = "Name for quiz ArgoCD application"
  default     = "quiz-app"
}

variable "quiz_path" {
  type        = string
  description = "Path for quiz applications in git repository"
  default     = "quiz-apps"
}

variable "quiz_namespace" {
  type        = string
  description = "Kubernetes namespace for quiz applications"
  default     = "quiz-app"
}