#!/bin/bash
# Deploy the ML Recommendation Platform to Kubernetes

set -e

echo "Deploying ML Recommendation Platform to Kubernetes..."

# Check if required tools are available
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is required but not installed."
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo "Error: Helm is required but not installed."
    exit 1
fi

# Configure AWS credentials if deploying to AWS (optional)
# Uncomment and set the following lines if deploying to AWS EKS
# echo "Configuring AWS credentials..."
# export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
# export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
# export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}
# aws eks update-kubeconfig --name ${EKS_CLUSTER_NAME} --region ${AWS_DEFAULT_REGION}

# Add the platform chart repository (if not already added)
helm repo add recommendation-platform ./charts/recommendation-platform || true
helm repo update

# Deploy or upgrade the release
echo "Deploying/upgrading the recommendation platform..."
helm upgrade --install recommendation-platform ./charts/recommendation-platform \
  --namespace ml-platform --create-namespace \
  -f ./charts/recommendation-platform/values.yaml \
  --set image.tag=${GIT_SHA:-latest} \
  --set mlflow.trackingUri=http://mlflow.mlflow.svc.cluster.local:5000 \
  --wait \
  --timeout 5m

echo "Deployment initiated. Checking rollout status..."

# Check the rollout status of the deployment
kubectl rollout status deployment/recommendation-platform-api -n ml-platform --timeout=120s
kubectl rollout status deployment/recommendation-platform-consumer -n ml-platform --timeout=120s

echo "Deployment completed successfully!"

# Optionally, show the services
echo "Services:"
kubectl get services -n ml-platform

echo ""
echo "To access the API, you can use port forwarding:"
echo "  kubectl port-forward svc/recommendation-platform-api 8000:8000 -n ml-platform"
echo "Then visit http://localhost:8000/health"