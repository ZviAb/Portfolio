# OIDC Identity Provider for EKS
# Required for IAM roles for service accounts (IRSA)
data "tls_certificate" "eks" {
  url = var.cluster_oidc_issuer_url
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = var.cluster_oidc_issuer_url

  tags = merge(
    var.resource_tags,
    {
      Name = "${var.project_prefix}-${terraform.workspace}-eks-oidc"
    }
  )
}

# IAM Role for EBS CSI Driver
# Allows the EBS CSI driver to manage EBS volumes
data "aws_iam_policy_document" "ebs_csi_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:ebs-csi-controller-sa"]
    }
    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ebs_csi" {
  name               = "${var.project_prefix}-${terraform.workspace}-ebs-csi-driver"
  assume_role_policy = data.aws_iam_policy_document.ebs_csi_assume_role.json

  tags = merge(
    var.resource_tags,
    {
      Name = "${var.project_prefix}-${terraform.workspace}-ebs-csi-driver"
    }
  )
}

# Use AWS managed policy for EBS CSI driver
resource "aws_iam_role_policy_attachment" "ebs_csi" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
  role       = aws_iam_role.ebs_csi.name
}

# EBS CSI Driver Add-on
# Enables EBS volume provisioning for persistent storage
resource "aws_eks_addon" "ebs_csi" {
  cluster_name             = var.cluster_name
  addon_name               = "aws-ebs-csi-driver"

  service_account_role_arn = aws_iam_role.ebs_csi.arn
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  tags = merge(
    var.resource_tags,
    {
      Name = "${var.project_prefix}-${terraform.workspace}-ebs-csi-addon"
    }
  )

  depends_on = [
    aws_iam_role_policy_attachment.ebs_csi
  ]
}

# Default StorageClass for EBS GP3 volumes
# Provides high-performance, cost-effective storage for workloads
resource "kubernetes_storage_class" "ebs_gp3" {
  metadata {
    name = "gp3"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
  }
  storage_provisioner    = "ebs.csi.aws.com"
  volume_binding_mode    = "WaitForFirstConsumer"
  allow_volume_expansion = true
  parameters = {
    type   = "gp3"
    fsType = "ext4"
  }

  depends_on = [aws_eks_addon.ebs_csi]
}