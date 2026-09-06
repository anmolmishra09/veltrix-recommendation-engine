# Recommendation Platform Helm Chart

This Helm chart provides a production-ready deployment of the recommendation platform.

## Installation

```bash
helm install recommendation-platform ./recommendation-platform
```

## Configuration

The following tables list the configurable parameters of the recommendation-platform chart and their default values.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replica pods | `2` |
| `image.repository` | Image repository | `recommendation-platform` |
| `image.tag` | Image tag | `latest` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |

## Configuration Values

The chart includes a comprehensive configuration section that mirrors the application's environment variables:

- `config.ENVIRONMENT`: Application environment (`production`)
- `config.DEBUG`: Debug mode (`false`)
- `config.DATABASE_URL`: PostgreSQL connection string
- And many more...

## Secrets

The chart includes a secrets section for sensitive values:
- `secrets.POSTGRES_PASSWORD`: PostgreSQL password
- `secrets.REDIS_PASSWORD`: Redis password
- And others...

These should be overridden in production with actual secret values.

## Persistence

The chart includes a persistent volume claim for model storage:
- Size: 10Gi
- Access mode: ReadWriteOnce

## Resources

Resource requests and limits are configurable:
- Requests: 250m CPU, 256Mi RAM
- Limits: 500m CPU, 512Mi RAM

## Autoscaling

Horizontal Pod Autoscaler is enabled by default:
- Minimum replicas: 2
- Maximum replicas: 10
- Target CPU utilization: 70%
- Target memory utilization: 80%

## Documentation

For more information, please see the [main documentation](../README.md).