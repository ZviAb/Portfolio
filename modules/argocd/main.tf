terraform {
  required_providers {
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = "~> 1.14.0"
    }
  }
}


resource "helm_release" "argocd" {
  name       = "argocd"
  namespace  = "argocd"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  version    = "6.7.12"

  create_namespace = true
  replace         = true

  values = [
    yamlencode({
      configs = {
        secret = {
          argocdServerAdminPassword = bcrypt(jsondecode(data.aws_secretsmanager_secret_version.argocd_ssh_key.secret_string)["argocd_password"])
        }
      }
    })
  ]

}

data "aws_secretsmanager_secret" "argocd_ssh_key" {
  name = var.aws_secrets_name
}

data "aws_secretsmanager_secret_version" "argocd_ssh_key" {
  secret_id = data.aws_secretsmanager_secret.argocd_ssh_key.id
}

resource "kubernetes_secret" "argocd_repo_ssh" {
  metadata {
    name      = "repo-gitlab-ssh"
    namespace = "argocd"
    labels = {
      "argocd.argoproj.io/secret-type" = "repository"
    }
  }
  data = {
    type          = "git"
    url           = var.git_repo_url
    sshPrivateKey = jsondecode(data.aws_secretsmanager_secret_version.argocd_ssh_key.secret_string)["SshKey"]
  }
  type = "Opaque"
  depends_on = [helm_release.argocd]
}

resource "kubectl_manifest" "argocd_application_infra_app" {
  yaml_body = templatefile("${path.module}/templates/infra-app-parent.yaml", {
    name            = var.infra_app_name
    namespace       = "argocd"
    repo_url        = var.git_repo_url
    infra_namespace = "argocd"
    infra_path      = var.infra_path
  })
  
  depends_on = [helm_release.argocd, kubernetes_secret.argocd_repo_ssh]
}

resource "kubectl_manifest" "argocd_application_quiz_app" {
  yaml_body = templatefile("${path.module}/templates/quiz-app-parent.yaml", {
    name           = var.quiz_app_name
    namespace      = "argocd"
    repo_url       = var.git_repo_url
    quiz_namespace = var.quiz_namespace
    quiz_path      = var.quiz_path
  })
  
  depends_on = [kubectl_manifest.argocd_application_infra_app]
}