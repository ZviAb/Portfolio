# Quiz App - Kubernetes Deployment with Argo CD

This repository contains a complete Kubernetes deployment for a Quiz Application using the App of Apps pattern with Argo CD. It manages both the main quiz application and all necessary infrastructure components, including ingress controller, cert-manager, monitoring stack (Prometheus, Grafana), logging (Elasticsearch, Fluent Bit, Kibana), and more.

## Table of Contents

- [Project Structure](#project-structure)
- [Key Features](#key-features)
- [Technologies Stack](#technologies-stack)
- [Quick Start](#quick-start)
- [Accessing the Application and Services](#accessing-the-application-and-services)
- [Useful Commands](#useful-commands)
- [Security Features](#security-features)
- [GitOps Workflow](#gitops-workflow)
- [Customization](#customization)
- [Author](#author)


## Project Structure

```
.
├── Application-parent.yaml          # Argo CD Application for main quiz app
├── infra-app-parent.yaml          # Argo CD App of Apps for infrastructure
│
├── application/                    # Quiz App Helm chart
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── ingress.yaml
│       ├── cluster-issuer.yaml
│       ├── externalsecret.yaml     # External secrets for DB credentials
│       └── secretstore.yaml       # AWS Secrets Manager integration
│
└── infra-apps/                    # Infrastructure components
    ├── cert-manager.yaml          # TLS certificate management
    ├── external-secrets.yml       # External Secrets Operator
    ├── ingress-controller.yaml    # NGINX Ingress Controller
    │
    ├── logging/                   # Logging stack
    │   ├── elasticsearch.yaml
    │   ├── fluent-bit.yaml
    │   ├── kibana.yaml
    │   ├── externalsecret.yaml
    │   └── secretstore.yaml
    ├── logging.yaml               # Logging App of Apps
    │
    ├── monitoring/                # Monitoring stack
    │   ├── kube-prometheus-stack.yaml
    │   ├── externalsecret.yaml
    │   └── secretstore.yaml
    └── monitoring.yaml            # Monitoring App of Apps
```

## Key Features

**Components**

- Quiz Application: Flask quiz app with PostgreSQL HA backend
- Infrastructure: Core Kubernetes services (Ingress, Cert-Manager, Logging, Monitoring)
- Monitoring: Prometheus & Grafana integration with custom metrics
- Security: TLS certificates via Let's Encrypt, AWS Secrets Manager integration

## Technologies Stack

- **Kubernetes** - Container orchestration
- **Helm** - Package manager for Kubernetes
- **Argo CD** - GitOps continuous delivery
- **PostgreSQL HA** - High availability database
- **NGINX Ingress** - Ingress controller
- **cert-manager** - Automatic TLS certificates
- **External Secrets Operator** - AWS Secrets Manager integration
- **Prometheus & Grafana** - Monitoring and alerting
- **Elasticsearch, Fluent Bit, Kibana** - Logging stack

## Quick Start

### Prerequisites

- Kubernetes cluster with ArgoCD installed
- AWS Secrets Manager with required secrets
- Container registry access (ECR)

### Deploy the Application

1. **Deploy Infrastructure Apps:**

   ```bash
   kubectl apply -f infra-app-parent.yaml
   ```

2. **Deploy Quiz Application:**
   ```bash
   kubectl apply -f Application-parent.yaml
   ```

## Accessing the Application and Services

### Quiz Application

The quiz app is accessible at:

- **https://www.zvidevops.cloud**
- **https://zvidevops.cloud**

### Grafana (Monitoring)

Access Grafana dashboard:

```bash
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring
```

Then visit http://localhost:3000

- Username: `admin`
- Password: Retrieved from `monitoring-secret`

### Kibana (Logging)

Access Kibana dashboard:

```bash
kubectl port-forward svc/kibana-kibana 5601:5601 -n logging
```

Then visit http://localhost:5601

- Username: `elastic`
- Password: Retrieved from `logging-secret`

## Useful Commands

```bash
# Check all Argo CD applications status
kubectl get applications -n argocd

# Check quiz app pods
kubectl get pods -n quizapp

# View quiz app logs
kubectl logs -l app=quiz-app -n quizapp -f

# Check database connection
kubectl get pods -l app.kubernetes.io/name=postgresql-ha -n quizapp

# View ingress status
kubectl get ingress -n quizapp

# Check certificates
kubectl get certificates -n quizapp

# Monitor external secrets
kubectl get externalsecrets -A

# Check Prometheus targets
kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring
```

## Security Features

- **TLS/SSL** - Automatic certificate management
- **External Secrets** - Secure secret management with AWS
- **JWT Authentication** - Secure user sessions

## GitOps Workflow

This project follows GitOps principles with a complete CI/CD pipeline:

### 1. Code Changes

- **Push to GitLab Repository**: Developer commits code changes to GitLab
- **CI Pipeline Trigger**: GitLab CI automatically triggers on code push
- **Build & Test**: Application is built, tested, and Docker image is created
- **Image Push**: New Docker image pushed to ECR registry

### 2. ArgoCD Sync

- **Automatic Detection**: ArgoCD monitors GitLab repository for manifest changes
- **Declarative Sync**: Automatically applies changes to match Git state
- **Image Update**: Pulls latest Docker image from ECR
- **Rolling Deployment**: Performs zero-downtime deployment

### 3. Health Monitoring

- **Continuous Application Health Checks**: ArgoCD monitors pod and service health
- **Resource Status Tracking**: Real-time status of all Kubernetes resources
- **Readiness & Liveness Probes**: Application health validation
- **Sync Status Monitoring**: Track deployment status across all applications

### 4. Auto-healing

- **Automatic Drift Correction**: Reverts manual changes to match Git state
- **Self-Healing Applications**: Automatically restarts failed pods
- **Configuration Drift Detection**: Identifies and corrects configuration drift
- **Rollback Capabilities**: Easy rollback to previous working states

### Complete Gitops Flow

```
Code Changes → ArgoCD Detection → K8s Deployment → Health Check → Auto-healing
```

## Customization

The main configuration is in `application/values.yaml`:

- **Domain**: Update `ingress.hosts` with your domain name
- **App Image**: Change `app.image.name` and `app.image.tag` for your container
- **Resources**: Adjust `app.resources` for CPU/memory limits
- **Database**: Configure `postgresql-ha` settings for your database needs
- **Secrets**: Update AWS Secrets Manager key `zvi/quizapp/key` with your credentials

## Author

Created by **Zvi Abramovich** - DevOps Engineer

- Email: zviabramovich22@gmail.com
- Domain: zvidevops.cloud

Feel free to reach out if you have questions or suggestions!
