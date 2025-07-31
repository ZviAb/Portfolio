variable "project_prefix" {
  type        = string
  description = "Prefix for naming all resources"
}

variable "resource_tags" {
  type        = map(string)
  description = "Common tags to apply to all resources"
}

variable "git_repo_url" {
  type        = string
  description = "Git repository URL for ArgoCD applications"
}

variable "aws_secrets_name" {
  type        = string
  description = "AWS Secrets Manager secret name containing SSH key and ArgoCD password"
}

variable "infra_app_name" {
  type        = string
  description = "Name for the infrastructure ArgoCD application"
  default     = "infra-apps"
}

variable "infra_path" {
  type        = string
  description = "Path in git repository for infrastructure applications"
  default     = "infra-apps"
}

variable "quiz_app_name" {
  type        = string
  description = "Name for the quiz ArgoCD application"
  default     = "quiz-app"
}

variable "quiz_path" {
  type        = string
  description = "Path in git repository for quiz applications"
  default     = "quiz-apps"
}

variable "quiz_namespace" {
  type        = string
  description = "Kubernetes namespace for quiz applications"
  default     = "quiz-app"
}