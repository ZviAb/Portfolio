# EKS Control Plane SG
resource "aws_security_group" "eks_cluster_sg" {
  name        = "${var.project_prefix}-${terraform.workspace}-eks-cluster-sg"
  description = "EKS Cluster Security Group"
  vpc_id      = var.vpc_id

  # Allow kubectl to access the EKS API server (HTTPS)
  ingress {
    description = "Allow access to EKS API"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] 
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_prefix}-${terraform.workspace}-eks-cluster-sg"
  }
}

# EKS Worker Nodes SG
resource "aws_security_group" "eks_nodes_sg" {
  name        = "${var.project_prefix}-${terraform.workspace}-eks-nodes-sg"
  description = "EKS Worker Nodes Security Group"
  vpc_id      = var.vpc_id

  # Node-to-Node communication (pods + kubelet)
  ingress {
    description = "Allow inter-node communication"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
  }

  # Allow traffic from control plane to worker nodes (kubelet, CNI, etc.)
  ingress {
    description     = "Allow control plane to communicate with nodes"
    from_port       = 1025
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_cluster_sg.id]
  }

  ingress {
    description     = "Allow control plane to communicate on 443 (webhooks etc)"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_cluster_sg.id]
  }

  # Allow EBS CSI driver to communicate with AWS APIs
  egress {
    description = "EBS CSI driver AWS API access"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_prefix}-${terraform.workspace}-eks-nodes-sg"
  }
}

# EKS Cluster IAM Role - allows EKS service to manage cluster resources
resource "aws_iam_role" "eks_cluster" {
  name = "${var.project_prefix}-${terraform.workspace}-eks-cluster-role"

  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })

  tags = var.resource_tags
}

# Attach required policies for EKS cluster management
resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

# Attach VPC resource controller policy for ENI management
resource "aws_iam_role_policy_attachment" "eks_vpc_resource_controller" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
  role       = aws_iam_role.eks_cluster.name
}

# EKS Node Group IAM Role - allows EC2 instances to join EKS cluster
resource "aws_iam_role" "eks_node_group" {
  name = "${var.project_prefix}-${terraform.workspace}-eks-node-group-role"

  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })

  tags = var.resource_tags
}

# Attach worker node policy for basic EKS node functionality
resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_node_group.name
}

# Attach CNI policy for pod networking
resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_node_group.name
}

# Attach ECR policy for pulling container images
resource "aws_iam_role_policy_attachment" "eks_container_registry_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_node_group.name
}

# Attach Secrets Manager policy for ArgoCD SSH keys and passwords
resource "aws_iam_role_policy_attachment" "eks_secrets_manager" {
  policy_arn = "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
  role       = aws_iam_role.eks_node_group.name
}

# Instance Profile for EKS Node Group - required for EC2 instances
resource "aws_iam_instance_profile" "eks_node_group" {
  name = "${var.project_prefix}-${terraform.workspace}-eks-node-group-profile"
  role = aws_iam_role.eks_node_group.name

  tags = var.resource_tags
}

