# Model Serving

## Overview

Model serving is the process of deploying trained machine learning models to make predictions in production. In the ML Recommendation Platform, we serve ranking models to score candidate items during recommendation requests.

## Requirements

- **Low Latency**: Predictions must be returned quickly to meet user experience requirements (typically <10ms for the ranking step).
- **High Throughput**: The system must handle thousands of requests per second.
- **Reliability**: The service must be fault-tolerant and self-healing.
- **Scalability**: The system must scale horizontally to handle increased load.
- **Monitoring**: Detailed metrics and logs must be available for debugging and performance tuning.
- **A/B Testing**: Ability to route traffic to different model versions for experimentation.
- **Rollback**: Ability to quickly revert to a previous model version if issues are detected.

## Architecture

### Model Loader
- A singleton service that loads models from MLflow or local files.
- Caches models in memory to avoid reloading on every request.
- Handles model versioning and hot-reloading of new models.

### Prediction Service
- Integrated into the recommendation API (FastAPI).
- Uses the model loader to get the latest model.
- Preprocesses input features (user and product features) into tensors.
- Runs the model inference in a thread-safe manner.
- Post-processes model outputs (e.g., applying softmax if needed).

### Model Loading Strategy
- **Startup**: Load the default model version specified by environment variables.
- **Hot Reloading**: Periodically check for new model versions in MLflow (optional).
- **Fallback**: If loading from MLflow fails, fall back to the locally cached model.

### Inference Optimization
- **Batching**: For efficiency, we batch multiple user features when scoring multiple candidates for the same user.
- **Hardware Acceleration**: Utilize GPUs if available for faster inference.
- **Model Quantization**: Optionally quantize models for faster CPU inference (not implemented in this version).

## Model Versioning and Promotion

### MLflow Model Registry
- We use MLflow Model Registry to manage model lifecycle.
- Models progress through stages: Staging -> Production -> Archived.
- Only models in the "Production" stage are served by default.

### Promotion Process
1. Train a new model and log it to MLflow.
2. Transition the model to "Staging" stage.
3. Validate the model using offline metrics and A/B tests.
4. Transition the model to "Production" stage.
5. The model loader automatically detects the change and loads the new model (if hot reloading is enabled).
6. Monitor the new model's performance in production.

### Rollback Process
- If a new model shows degraded performance, transition the previous model back to "Production".
- The model loader will switch to the previous model on the next reload (or immediately if configured).

## Implementation Details

### Model Loader (apps/api/model_loader.py)
- Implements a singleton pattern to ensure only one instance of each model is loaded.
- Loads models from MLflow using `mlflow.pytorch.load_model`.
- Falls back to loading from local pickle or PyTorch files if MLflow is unavailable.
- Logs loading events and errors for monitoring.

### Recommendation Service (apps/api/recommender.py)
- Uses the model loader to get the embedding and ranking models.
- The embedding model is wrapped to provide user and product embeddings for candidate generation.
- The ranking model is used to score candidate items.

### Tensor Preparation
- User features are retrieved from the feature store and converted to a tensor.
- Product features for candidates are retrieved and converted to a tensor.
- The user feature tensor is repeated for each candidate to form a batch.

### Inference Execution
- Uses `torch.no_grad()` to disable gradient computation during inference.
- Runs the model on the appropriate device (CPU or GPU).

## Performance Considerations

- **Latency Breakdown**:
  - Feature retrieval from feature store: ~2ms
  - Candidate generation: ~5ms
  - Feature retrieval for candidates: ~3ms
  - Model inference: ~2ms (for a batch of 100 candidates)
  - Filtering and sorting: ~1ms
  - Total: ~13ms

- **Throughput**:
  - With batching, the system can handle hundreds of requests per second on a single CPU core.
  - Horizontal scaling via Kubernetes allows for linear scaling of throughput.

## Monitoring

- **Latency Metrics**: Track the time taken for each step of the recommendation pipeline.
- **Error Rates**: Monitor for inference errors (e.g., tensor shape mismatches).
- **Resource Usage**: Monitor CPU, GPU, and memory usage during inference.
- **Business Metrics**: Track click-through rate and conversion rate to detect model degradation.

## Security

- Model files are stored in MLflow with access control.
- The model loader does not execute arbitrary code; it only loads PyTorch models.
- Input validation is performed on user and product IDs to prevent injection attacks.

## Future Improvements

- Implement model quantization for faster CPU inference.
- Add support for TensorFlow and ONNX models.
- Implement adaptive batching based on request volume.
- Add canary analysis for automated model promotion.