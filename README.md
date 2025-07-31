# AWS EKS Infrastructure with Argo CD

A production ready Infrastructure as Code (IaC) deploying Amazon EKS clusters with essential applications. This Terraform project provides a complete, modular infrastructure setup including networking, security, storage, and application deployment automation.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Modules](#modules)
- [Configuration](#configuration)
- [Deployed Applications](#deployed-applications)
- [Post-Deployment](#post-deployment)
- [Security Features](#security-features)
- [Cost Optimization](#cost-optimization)
- [Cleanup](#cleanup)
- [Support](#support)

## Overview

This Terraform project deploys a comprehensive AWS EKS infrastructure designed for production workloads with GitOps automation. The infrastructure includes:

- **Networking Layer**: Multi-AZ VPC with public/private subnets and NAT Gateway
- **Compute Layer**: EKS cluster (v1.32) with auto-scaling managed node groups
- **Security Layer**: IAM roles, security groups, and RBAC configurations
- **Storage Layer**: EBS CSI driver with GP3 storage classes
- **GitOps Layer**: Argo CD for continuous deployment and application management

## Features

**Modular Design**: Reusable Terraform modules for easy customization  
**GitOps Integration**: Automated application deployment with Argo CD  
**Security First**: IAM roles, private subnets, encrypted storage, and AWS Secrets Manager integration  
**Cost Optimized**: Right-sized instances and efficient resource allocation

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) >= 1.0
- [AWS CLI](https://aws.amazon.com/cli/) configured with credentials
- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- Access to AWS account with appropriate permissions
- S3 bucket for Terraform state (configured in `providers.tf`)

### Provider Versions

- AWS Provider: `~> 5.0`
- Kubernetes Provider: `~> 2.38`
- Helm Provider: `~> 3.0`
- Kubectl Provider: `~> 1.14.0`

## Project Structure

```
.
├── main.tf                     # Root module orchestration
├── variables.tf                # Input variables
├── providers.tf                # Provider configurations
├── terraform.tfvars.example   # Variable values template
├── modules/
│   ├── network/               # VPC, subnets, routing
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   └── variables.tf
│   ├── security/              # IAM roles and security groups
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   └── variables.tf
│   ├── eks/                   # EKS cluster and node groups
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   └── variables.tf
│   ├── ebs-csi/              # EBS CSI driver and IRSA
│   │   └── main.tf
│   └── argocd/               # ArgoCD deployment and apps
│       ├── main.tf
│       ├── variables.tf
│       └── templates/
│           ├── infra-app-parent.yaml
│           └── quiz-app-parent.yaml
```

## Quick Start

```bash
# Clone and navigate to project
git clone <repository-url>
cd aws-eks-argocd-infrastructure

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var-file="terraform.tfvars"

# Deploy infrastructure
terraform apply -var-file="terraform.tfvars"
```

## Modules

### Network Module

- Creates VPC with configurable CIDR blocks
- Public subnet with Internet Gateway
- Private subnets with NAT Gateway
- Route tables and associations

### Security Module

- EKS cluster service role
- Node group instance role
- Security groups for cluster and nodes
- AWS managed policy attachments

### EKS Module

- EKS cluster with API authentication mode
- Managed node group (t3a.medium instances)
- Cluster addons: VPC CNI, CoreDNS, Kube-proxy
- Automatic kubeconfig update

### EBS CSI Module

- EBS CSI driver addon
- IRSA (IAM Roles for Service Accounts)
- Service account with IAM role annotations

### ArgoCD Module

- ArgoCD deployment via Helm
- GitLab repository integration
- Parent applications for infrastructure and quiz apps
- SSH key management via AWS Secrets Manager

## Configuration

### Customization

Edit `terraform.tfvars` to modify:

- VPC CIDR blocks and subnets
- EKS node group scaling parameters
- Resource tags and naming
- ArgoCD application configurations

### Key Variables

| Variable              | Description                   | Default/Example                |
| --------------------- | ----------------------------- | ------------------------------ |
| `aws_region`          | AWS region                    | `ap-south-1`                   |
| `project_prefix`      | Resource naming prefix        | `QuizApp`                      |
| `vpc_cidr_block`      | VPC CIDR block                | `10.0.0.0/16`                  |
| `subnet_count`        | Number of subnets to create   | `2`                            |
| `kubernetes_version`  | Kubernetes version            | `1.32`                         |
| `node_instance_types` | Instance types for nodes      | `["t3a.medium"]`               |
| `desired_capacity`    | Desired number of nodes       | `3`                            |
| `max_capacity`        | Maximum number of nodes       | `3`                            |
| `min_capacity`        | Minimum number of nodes       | `1`                            |
| `git_repo_url`        | Git repository URL for ArgoCD | `git@gitlab.com:user/repo.git` |
| `aws_secrets_name`    | AWS Secrets Manager secret    | `zvi/quizapp/key`              |
| `infra_app_name`      | Infrastructure app name       | `infra-app-of-apps`            |
| `infra_path`          | Infrastructure apps path      | `infra-apps`                   |
| `quiz_app_name`       | Quiz application name         | `quizapp`                      |
| `quiz_path`           | Quiz application path         | `application`                  |
| `quiz_namespace`      | Quiz app Kubernetes namespace | `quizapp`                      |



## Post-Deployment

### Access Cluster

```bash
aws eks update-kubeconfig --region ap-south-1 --name <cluster-name>
```

### Verify Applications

```bash
kubectl get pods -n argocd
kubectl get applications -n argocd
```

### ArgoCD Access

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Access: https://localhost:8080
# Username: admin
# Password: Set in AWS Secrets Manager
```

## Security Features

- Private subnets for worker nodes
- IAM roles with least-privilege permissions
- Security groups with restricted access
- SSH keys managed via AWS Secrets Manager
- Network isolation and encrypted communication

## Cost Optimization

- T3a.medium instances for cost-effectiveness
- Configurable node group scaling
- EBS GP3 storage for better price/performance

## Cleanup

```bash
terraform destroy -var-file="terraform.tfvars"
```

**Note**: Ensure all LoadBalancer services and persistent volumes are removed before destroying infrastructure to avoid orphaned AWS resources.

## Author

Created by **Zvi Abramovich** - DevOps Engineer

- Email: zviabramovich22@gmail.com
- Domain: zvidevops.cloud

Feel free to reach out if you have questions or suggestions!
