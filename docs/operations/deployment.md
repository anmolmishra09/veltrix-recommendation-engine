# Deployment

## Overview

This document describes how to deploy the ML Recommendation Platform to various environments, including local development, staging, and production. The platform is designed to be deployed using Docker and Kubernetes, with infrastructure provisioned via Terraform.

## Prerequisites

### Tools
- Docker 20.10+
- kubectl 1.21+
- Helm 3.0+
- Terraform 1.0+
- AWS CLI (if deploying to AWS)
- Python 3.9+
- Git

### Accounts and Permissions
- AWS account with permissions to create EC2, VPC, EKS, RDS, S3, IAM resources.
- Docker Hub account (for storing custom images).
- MLflow tracking server (can be self-hosted or use a managed service).
- Monitoring stack (Prometheus, Grafana, Jaeger) - can be deployed via Helm or use managed services.

## Deployment Strategies

### 1. Local Development (Docker Compose)
- **Purpose**: For developers to test changes locally.
- **Components**: All services run in Docker containers on a single machine.
- **Data**: Uses local SQLite or PostgreSQL for the feature store, and local disk for MLflow artifacts.
- **Command**: `docker-compose up`

### 2. Staging Environment
- **Purpose**: For integration testing, performance testing, and pre-production validation.
- **Components**: Deployed to a Kubernetes cluster (can be minimal size).
- **Data**: Uses managed services (e.g., Amazon RDS for PostgreSQL, Amazon ElastiCache for Redis).
- **Infrastructure**: Provisioned via Terraform (see `infrastructure/terraform/environments/staging`).
- **Deployment**: Helm charts or Kubernetes manifests.

### 3. Production Environment
- **Purpose**: For serving live user traffic.
- **Components**: Deployed to a production-sized Kubernetes cluster.
- **Data**: Uses highly available and scaled managed services.
- **Infrastructure**: Provisioned via Terraform (see `infrastructure/terraform/environments/production`).
- **Deployment**: Helm charts with production-grade settings (e.g., resource limits, replicas, pod disruption budgets).

## Deployment Process

### Step 1: Provision Infrastructure
```bash
# Navigate to the environment directory
cd infrastructure/terraform/environments/<env>  # e.g., dev, staging, production

# Initialize Terraform (if not already initialized)
terraform init

# Review the plan
terraform plan

# Apply the changes
terraform apply -auto-approve
```

### Step 2: Deploy Supporting Services
Deploy services that are not part of the main application chart (e.g., MLflow, monitoring stack).

#### MLflow
```bash
helm repo add mlflow https://mlflow.org
helm upgrade --install mlflow mlflow/mlflow \
  --namespace mlflow --create-namespace \
  -f values-mlflow.yaml
```

#### Monitoring Stack (Prometheus, Grafana, Jaeger)
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts

# Deploy Prometheus
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  -f values-prometheus.yaml

# Deploy Grafana (if not included in the kube-prometheus-stack)
helm upgrade --install grafana grafana/grafana \
  --namespace monitoring --create-namespace \
  -f values-grafana.yaml

# Deploy Jaeger
helm upgrade --install jaeger jaegertracing/jaeger \
  --namespace monitoring --create-namespace \
  -f values-jaeger.yaml
```

### Step 3: Deploy the Recommendation Platform
```bash
# Add the platform chart repository (if not already added)
helm repo add recommendation-platform ./charts/recommendation-platform

# Update dependencies
helm dependency update ./charts/recommendation-platform

# Deploy or upgrade the release
helm upgrade --install recommendation-platform ./charts/recommendation-platform \
  --namespace ml-platform --create-namespace \
  -f values.yaml \
  --set image.tag=$(git rev-parse --short HEAD) \
  --set mlflow.trackingUri=http://mlflow.mlflow.svc.cluster.local:5000
```

### Step 4: Verify Deployment
```bash
# Check that all pods are running
kubectl get pods -n ml-platform

# Check the services
kubectl get services -n ml-platform

# Test the API
export API_URL=$(kubectl get svc recommendation-platform-api -n ml-platform -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl -s $API_URL/health
```

### Step 5: Initialize Data
```bash
# Seed the database with initial users and products
kubectl exec -n ml-platform -it $(kubectl get pod -n ml-platform -l app=recommendation-platform-api -o jsonpath='{.items[0].metadata.name}') -- python scripts/seed_data.py

# Train initial models (if not done already)
kubectl exec -n ml-platform -it $(kubectl get pod -n ml-platform -l app=recommendation-platform-api -o jsonpath='{.items[0].metadata.name}') -- python ml/train.py
```

## Configuration Management

### Environment-Specific Values
- Each environment (dev, staging, production) has its own `values.yaml` file in the Helm chart.
- These files override default values in `charts/recommendation-platform/values.yaml`.

### Secrets Management
- Secrets (e.g., database passwords, API keys) are stored in Kubernetes secrets.
- They are referenced in the Helm chart using `{{ .Values.secrets.<key> }}`.
- Secrets can be managed using:
  - `kubectl create secret`
  - External secret managers (e.g., AWS Secrets Manager, HashiCorp Vault)
  - Helm secrets plugins

### Configuration Files
- Application configuration is managed via Python files or environment variables.
- The `apps/api/app/core/config.py` file loads settings from environment variables.
- Environment-specific settings are set in the Helm chart's `values.yaml` under `env`.

## Rolling Updates and Rollbacks

### Rolling Updates
- Helm automatically performs rolling updates when the chart is upgraded.
- The `maxSurge` and `maxUnavailable` parameters in the deployment control how many pods can be unavailable during the update.

### Rollbacks
- To rollback to a previous release:
  ```bash
  helm rollback recommendation-platform <revision-number> -n ml-platform
  ```
- To view revision history:
  ```bash
  helm history recommendation-platform -n ml-platform
  ```

## Scaling

### Horizontal Pod Autoscaler (HPA)
- The platform chart includes an HPA definition that scales the API service based on CPU utilization or custom metrics (e.g., request rate).
- Example HPA configuration:
  ```yaml
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 80
  ```

### Vertical Pod Autoscaler (VPA)
- Can be used to automatically adjust CPU and memory requests based on actual usage.
- Requires installing the VPA admission controller.

## Blue/Green Deployment (Optional)

For zero-downtime deployments with instant rollback capability, we can use a blue/green deployment strategy.

### Implementation
1. Deploy the new version as a separate release (e.g., `recommendation-platform-green`).
2. Switch the service to point to the new release.
3. Monitor the new release for issues.
4. If successful, delete the old release; otherwise, switch back to the old release.

### Tools
- Argo Rollouts or Flagger can automate blue/green and canary deployments.

## Database Migrations

### Approach
- We use Alembic for database migrations (if using SQLAlchemy) or manual SQL scripts.
- Migrations are applied as part of the deployment process using a `helm hook`.

### Example
```yaml
# In the Helm chart, a hook to run migrations
apiVersion: batch/v1
kind: Job
metadata:
  name: "{{ .Release.Name }}-db-migrate"
  annotations:
    "helm.sh/hook": pre-install,pre-upgrade
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        command: ["python", "scripts/migrate_db.py"]
        envFrom:
        - secretRef:
            name: "{{ .Release.Name }}-secrets"
      restartPolicy: OnFailure
  backoffLimit: 2
```

## Backup and Disaster Recovery

### Database
- Enable automated backups for managed RDS instances.
- For self-managed databases, use `pg_dump` and schedule regular backups to S3.

### Feature Store
- The offline store in S3 serves as a backup of the feature values.
- The online store (Redis) can be persisted to disk and snapshotted.

### MLflow
- The MLflow tracking server's backend store (e.g., PostgreSQL) should be backed up regularly.
- Artifacts stored in S3 are inherently durable.

### Configuration
- Store Terraform state in a remote backend (e.g., S3 with state locking).
- Keep a copy of the Helm chart values and Kubernetes manifests in version control.

## Monitoring and Logging

### Health Checks
- The platform includes liveness and readiness probes for Kubernetes.
- Liveness probe: `GET /health` (returns 200 if the service is running).
- Readiness probe: `GET /ready` (returns 200 if the service is ready to serve traffic).

### Metrics
- The platform exposes Prometheus metrics at `/metrics`.
- Key metrics include request latency, error rates, cache hit ratios, and model inference latency.

### Logs
- All services log to stdout/stderr, which is collected by the logging stack (Fluentd -> Elasticsearch -> Kibana).
- Logs are structured as JSON for easy querying.

## Troubleshooting

### Common Issues
- **ImagePullBackOff**: Check that the image name and tag are correct, and that the node has permission to pull from the registry.
- **CrashLoopBackOff**: Check the logs of the crashing pod (`kubectl logs <pod-name>`).
- **Service Unavailable**: Check that the service is exposed correctly (e.g., LoadBalancer or Ingress) and that the endpoints are registered.
- **High Latency**: Check metrics to identify bottlenecks (e.g., feature store latency, model inference time).
- **Pods Not Scheduling**: Check resource requests/limits and node availability.

### Commands for Debugging
```bash
# Get pod logs
kubectl logs -n ml-platform <pod-name>

# Describe a pod
kubectl describe -n ml-platform pod <pod-name>

# Exec into a pod
kubectl exec -n ml-platform -it <pod-name> -- /bin/sh

# Port-forward a service for local testing
kubectl port-forward -n ml-platform svc/recommendation-platform-api 8080:80

# Check events
kubectl get events -n ml-platform --sort-by='.metadata.timestamp'
```