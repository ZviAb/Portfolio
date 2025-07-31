output "oidc_provider_arn" {
  description = "ARN of the OIDC Provider for EKS"
  value       = aws_iam_openid_connect_provider.eks.arn
}

output "ebs_csi_driver_role_arn" {
  description = "ARN of the EBS CSI driver IAM role"
  value       = aws_iam_role.ebs_csi.arn
}

output "ebs_csi_addon_arn" {
  description = "ARN of the EBS CSI driver addon"
  value       = aws_eks_addon.ebs_csi.arn
}