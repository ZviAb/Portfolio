# EKS Cluster
# Note: Depends on IAM role from security module via var.cluster_role_arn
resource "aws_eks_cluster" "main" {
  name     = "${var.project_prefix}-${terraform.workspace}-eks-cluster"
  role_arn = var.cluster_role_arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = concat(var.private_subnet_ids)
    security_group_ids      = [var.cluster_security_group_id]
    endpoint_private_access = true
    endpoint_public_access  = true
  }

  tags = merge(
    var.resource_tags,
    {
      Name = "${var.project_prefix}-${terraform.workspace}-eks-cluster"
    }
  )
}

# EKS Node Group  
# Note: Depends on IAM role from security module via var.node_group_role_arn
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.project_prefix}-${terraform.workspace}-node-group"
  node_role_arn   = var.node_group_role_arn
  subnet_ids      = var.private_subnet_ids
  instance_types  = var.node_instance_types
  capacity_type   = var.capacity_type
  ami_type        = var.ami_type
  disk_size       = var.disk_size

  scaling_config {
    desired_size = var.desired_capacity
    max_size     = var.max_capacity
    min_size     = var.min_capacity
  }

  update_config {
    max_unavailable = var.max_unavailable
  }

  tags = merge(
    var.resource_tags,
    {
      Name = "${var.project_prefix}-${terraform.workspace}-node-group"
    }
  )
}
# Get cluster authentication token for providers
data "aws_eks_cluster_auth" "this" {
  name = aws_eks_cluster.main.id
}

# Update local kubeconfig automatically after cluster creation
resource "null_resource" "update_kubeconfig" {
  depends_on = [aws_eks_node_group.main]
  
  provisioner "local-exec" {
    command = "aws eks update-kubeconfig --region ${data.aws_region.current.name} --name ${aws_eks_cluster.main.name}"
  }
  
  triggers = {
    cluster_name     = aws_eks_cluster.main.name
    cluster_endpoint = aws_eks_cluster.main.endpoint
  }
}

# Get current AWS region for kubeconfig update
data "aws_region" "current" {}



