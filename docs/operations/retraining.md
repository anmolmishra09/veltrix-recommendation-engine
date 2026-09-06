# Model Retraining

## Overview

Model retraining is the process of periodically updating machine learning models with new data to maintain or improve their performance over time. This is essential because user preferences, item popularity, and market trends change, causing models to degrade if not retrained.

## Why Retrain?

### Concept Drift
- The relationship between features and the target variable changes over time.
- Example: During holiday seasons, purchasing behavior shifts significantly.

### Data Drift
- The distribution of input features changes over time.
- Example: New product categories are introduced, or user demographics shift.

### Model Decay
- Even without drift, models can degrade due to overfitting to historical patterns that no longer hold.

## Retraining Strategies

### 1. Time-Based Retraining
- **Description**: Retrain models on a fixed schedule (e.g., daily, weekly, monthly).
- **Pros**: Simple to implement and manage.
- **Cons**: May retrain too frequently (wasting resources) or not frequently enough (missing important changes).
- **Use Case**: Stable environments with predictable patterns.

### 2. Performance-Based Retraining
- **Description**: Retrain models when performance metrics drop below a threshold.
- **Pros**: Efficiently uses resources by retraining only when needed.
- **Cons**: Requires continuous monitoring and a reliable way to measure performance in production.
- **Use Case**: Environments with concept drift that can be detected via performance metrics.

### 3. Trigger-Based Retraining
- **Description**: Retrain models in response to specific events (e.g., new product launch, major marketing campaign).
- **Pros**: Ensures models are up-to-date for important events.
- **Cons**: Requires identifying and defining relevant triggers.
- **Use Case**: Events that are known to significantly impact user behavior.

### 4. Hybrid Approach
- **Description**: Combine time-based and performance-based strategies (e.g., retrain weekly, but also trigger retraining if performance drops).
- **Pros**: Balances reliability and efficiency.
- **Cons**: More complex to implement.

## Implementation in This Platform

We use a time-based retraining strategy with a weekly schedule, supplemented by performance-based triggers for critical issues.

### Retraining Pipeline
1. **Data Preparation**
   - Extract historical interaction data from the data lake (e.g., S3) for a defined window (e.g., last 90 days).
   - Generate features using the same feature pipelines used in production (to ensure consistency).
   - Store features in the feature store's offline store.

2. **Model Training**
   - Train new models using the prepared features.
   - Experiment with different algorithms, hyperparameters, and feature sets.
   - Validate models using a hold-out set from the same time period.
   - Log models, metrics, and artifacts to MLflow.

3. **Model Validation**
   - Compare the new model's performance to the current production model using offline metrics.
   - Check for data drift and concept drift using tools like Evidently.
   - Run statistical significance tests to confirm improvements.

4. **Model Promotion**
   - If the new model meets the promotion criteria, transition it to "Staging" in the MLflow Model Registry.
   - Optionally run an A/B test to validate in production.
   - If successful, transition the model to "Production".

5. **Model Serving**
   - The model loader in the recommendation API periodically checks for new models in the "Production" stage.
   - Upon detection, it loads the new model and begins using it for incoming requests.

### Retraining Frequency
- **Full Retraining**: Weekly (every Sunday at 3 AM UTC).
- **Incremental Updates**: Not implemented in this version (would require online learning algorithms).
- **Emergency Retraining**: Can be triggered manually via the `ml/retrain.py` script or through an Airflow DAG.

## Implementation Details

### Airflow DAGs
- The `dags/retraining_dag.py` file defines the Airflow DAG for retraining.
- The DAG includes tasks for:
  1. Data extraction
  2. Feature generation
  3. Model training
  4. Model validation
  5. Model promotion
  6. Notification

### MLflow Integration
- Models are logged to MLflow with the following metadata:
  - `training_start_date`, `training_end_date`
  - `feature_version` (hash of the feature definitions)
  - `algorithm` and `hyperparameters`
  - `metrics`: AUC, precision@K, recall@K, NDCG@K, etc.
  - `artifacts`: model file, feature importance plots, evaluation reports

### Model Loader (apps/api/model_loader.py)
- Checks for new models in the MLflow Model Registry at a configurable interval (default: every 60 minutes).
- Loads the latest version of the model in the "Production" stage.
- Falls back to the previously loaded model if the new model fails to load.
- Logs loading events and errors.

### Notification
- Success and failure notifications are sent via email or Slack.
- Notifications include:
  - Training start and end times
  - Model version and performance metrics
  - Any errors encountered during the pipeline

## Data Requirements

### Training Data Window
- The amount of historical data used for training affects model performance and training time.
- **Short Window (e.g., 7 days)**: Captures recent trends but may not generalize well.
- **Medium Window (e.g., 90 days)**: Balances recency and stability (used in this platform).
- **Long Window (e.g., 365 days)**: Captures long-term patterns but may include outdated behavior.

### Feature Consistency
- It is critical that the features used for training are identical to those used for serving.
- We ensure this by:
  1. Using the same feature store for both offline (training) and online (serving) access.
  2. Versioning feature definitions and tracking them with MLflow.
  3. Running the same feature generation code in both the retraining pipeline and the feature update pipelines.

## Handling Imbalanced Data

### Problem
- Interaction data is typically highly imbalanced (e.g., far more views than purchases, and most items have few interactions).

### Solutions
1. **Resampling**:
   - Oversample minority classes (e.g., purchases) or undersample majority classes (e.g., views).
   - Use techniques like SMOTE for generating synthetic samples.

2. **Weighted Loss Function**:
   - Assign higher weights to underrepresented classes in the loss function.
   - Example: In binary cross-entropy, weight the positive class by the inverse of its frequency.

3. **Stratified Sampling**:
   - Ensure that training batches contain a proportional representation of each class.

4. **Evaluation Metrics**:
   - Use metrics that are insensitive to class imbalance (e.g., AUC, precision@K, recall@K) rather than accuracy.

## Monitoring Retraining

### Metrics to Track
- **Training Time**: How long the training process takes.
- **Resource Usage**: CPU, GPU, memory, and disk usage during training.
- **Model Size**: Size of the saved model file.
- **Performance Metrics**: AUC, precision@K, recall@K, etc., on the validation set.
- **Data Drift Metrics**: Population Stability Index (PSI), Kolmogorov-Smirnov test, etc.
- **Concept Drift Metrics**: Changes in model coefficients or feature importance over time.

### Alerts
- **Training Failure**: If the training script exits with a non-zero status code.
- **Performance Degradation**: If the new model's validation metrics are worse than the current model by a threshold.
- **Data Drift Alert**: If the distribution of input features has shifted significantly.
- **Resource Alert**: If training exceeds allocated time or resources.

## Best Practices

### 1. Keep It Simple
- Start with a simple model and baseline features before adding complexity.
- Ensure that the retraining pipeline is reliable and reproducible before experimenting with complex models.

### 2. Version Everything
- Use Git for code and configuration.
- Use MLflow for models, parameters, and metrics.
- Use DVC or similar for large datasets (if needed).
- Use Terraform for infrastructure.

### 3. Automate and Schedule
- Use Airflow or Cron to automate the retraining pipeline.
- Ensure that the pipeline is idempotent and can be safely retried.

### 4. Validate Before Deploying
- Always validate new models offline before deploying to production.
- Consider using a canary release or A/B test before full promotion.

### 5. Monitor in Production
- Continuously monitor the performance of the deployed model.
- Be prepared to rollback if performance degrades unexpectedly.

### 6. Document Decisions
- Keep a changelog of model updates, including why a model was promoted or rejected.
- Document any changes to the feature set or training procedure.

## Example Retraining Command

```bash
# Manual retraining (for testing or emergencies)
python ml/retrain.py \
  --start-date 2026-06-01 \
  --end-date 2026-08-31 \
  --model-type ranking \
  --output-dir ./models
```

### Parameters
- `--start-date`: Start date for training data (inclusive).
- `--end-date`: End date for training data (inclusive).
- `--model-type`: Type of model to train (e.g., ranking, embedding).
- `--output-dir`: Directory to save the model and artifacts.

## Integration with CI/CD

The retraining pipeline can be integrated into the CI/CD system to automatically retrain models when code changes are detected.

### Example GitHub Actions Workflow
```yaml
name: Retrain Models

on:
  schedule:
    - cron: '0 3 * * 0'  # Weekly on Sunday at 3 AM
  workflow_dispatch:

jobs:
  retrain:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install mlflow boto3 evidently
    - name: Retrain models
      run: |
        python ml/retrain.py
    - name: Promote model to staging
      if: success()
      run: |
        python ml/promote_model.py --stage staging
    - name: Notify on failure
      if: failure()
      run: |
        # Send notification via Slack or email
        curl -X POST -H 'Content-type: application/json' \
          --data '{"text":"Model retraining failed"}'
          ${{ secrets.SLACK_WEBHOOK_URL }}
```