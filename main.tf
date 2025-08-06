# Get current public IP dynamically
data "http" "current_ip" {
  url = "https://checkip.amazonaws.com"
}

locals {
  current_ip_cidr = "${chomp(data.http.current_ip.response_body)}/32"
  # Combine dynamic IP with any additional static IPs
  admin_cidrs = concat(
    [local.current_ip_cidr],
    var.additional_admin_cidrs
  )
}

# Network module - creates VPC, subnets, and routing infrastructure
module "network" {
  source         = "./modules/network"
  vpc_cidr_block = var.vpc_cidr_block
  project_prefix = var.project_prefix
  resource_tags  = var.resource_tags
  subnet_count   = var.subnet_count
}

# Security module - creates IAM roles and security groups for EKS
module "security" {
  source            = "./modules/security"
  project_prefix    = var.project_prefix
  resource_tags     = var.resource_tags
  vpc_id            = module.network.vpc_id
  admin_cidr_blocks = local.admin_cidrs
}

# EKS module - creates the EKS cluster and managed node groups
module "eks" {
  source                    = "./modules/eks"
  project_prefix            = var.project_prefix
  resource_tags             = var.resource_tags
  private_subnet_ids        = module.network.private_subnet_ids
  cluster_role_arn          = module.security.eks_cluster_role_arn
  node_group_role_arn       = module.security.eks_node_group_role_arn
  cluster_security_group_id = module.security.eks_cluster_security_group_id
  nodes_security_group_id   = module.security.eks_nodes_security_group_id
  kubernetes_version        = var.kubernetes_version
  node_instance_types       = var.node_instance_types
  capacity_type             = var.capacity_type
  desired_capacity          = var.desired_capacity
  max_capacity              = var.max_capacity
  min_capacity              = var.min_capacity
}

# EBS CSI resources that depend on both security and EKS modules
module "ebs_csi" {
  source                   = "./modules/ebs-csi"
  project_prefix           = var.project_prefix
  resource_tags            = var.resource_tags
  cluster_name             = module.eks.cluster_id
  cluster_oidc_issuer_url  = module.eks.cluster_oidc_issuer_url
}

# ArgoCD module - depends on EKS cluster being ready
module "argocd" {
  source           = "./modules/argocd"
  project_prefix   = var.project_prefix
  resource_tags    = var.resource_tags
  git_repo_url     = var.git_repo_url
  aws_secrets_name = var.aws_secrets_name
  infra_app_name   = var.infra_app_name
  infra_path       = var.infra_path
  quiz_app_name    = var.quiz_app_name
  quiz_path        = var.quiz_path
  quiz_namespace   = var.quiz_namespace
}


output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_id
}




