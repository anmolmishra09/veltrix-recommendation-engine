"""
Data drift detection using Evidently.
"""
import pandas as pd
import numpy as np
import os
import logging
import json
from datetime import datetime
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset
from evidently.pipeline.column_mapping import ColumnMapping

logger = logging.getLogger(__name__)

def load_reference_data():
    """
    Load reference data (training data) for drift detection.
    """
    logger.info("Loading reference data")

    # In a real implementation, this would load the training data
    # For demonstration, we'll create dummy data
    np.random.seed(42)
    n_samples = 1000
    n_features = 10

    # Create reference data
    reference_data = pd.DataFrame({
        f'feature_{i}': np.random.randn(n_samples) for i in range(n_features)
    })

    # Add a target column for target drift detection
    reference_data['target'] = np.random.randint(0, 2, n_samples)

    return reference_data

def load_current_data():
    """
    Load current data (recent production data) for drift detection.
    """
    logger.info("Loading current data")

    # In a real implementation, this would load recent production data
    # For demonstration, we'll create data with some drift
    np.random.seed(43)  # Different seed to create drift
    n_samples = 800
    n_features = 10

    # Create current data with some drift in the first few features
    current_data = pd.DataFrame({
        f'feature_{i}': np.random.randn(n_samples) + (0.5 if i < 3 else 0) for i in range(n_features)
    })

    # Add a target column
    current_data['target'] = np.random.randint(0, 2, n_samples)

    return current_data

def detect_data_drift(reference_data: pd.DataFrame, current_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect data drift between reference and current data.

    Args:
        reference_data: Reference data (training data).
        current_data: Current data (production data).

    Returns:
        Dictionary of drift detection results.
    """
    logger.info("Detecting data drift")

    # Define column mapping
    # Assume all columns except 'target' are features
    feature_columns = [col for col in reference_data.columns if col != 'target']

    column_mapping = ColumnMapping()
    column_mapping.numerical_features = feature_columns
    column_mapping.target = 'target'

    # Create report
    data_drift_report = Report(metrics=[DataDriftPreset()])
    data_drift_report.run(reference_data=reference_data, current_data=current_data, column_mapping=column_mapping)

    # Get results as dictionary
    data_drift_result = data_drift_report.as_dict()

    # Also check target drift
    target_drift_report = Report(metrics=[TargetDriftPreset()])
    target_drift_report.run(reference_data=reference_data, current_data=current_data, column_mapping=column_mapping)
    target_drift_result = target_drift_report.as_dict()

    return {
        'data_drift': data_drift_result,
        'target_drift': target_drift_result,
        'timestamp': datetime.now().isoformat()
    }

def main():
    """
    Main function to run data drift detection.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("Starting data drift detection")

    # Load reference and current data
    reference_data = load_reference_data()
    current_data = load_current_data()

    # Detect drift
    drift_results = detect_data_drift(reference_data, current_data)

    # Save results
    output_dir = "./monitoring/evidently/reports"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"data_drift_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    with open(output_file, 'w') as f:
        json.dump(drift_results, f, indent=2)

    logger.info(f"Data drift report saved to {output_file}")

    # Print summary
    data_drift_metrics = drift_results['data drift']['metrics'][0]['result']
    target_drift_metrics = drift_results['target drift']['metrics'][0]['result']

    print("\n=== Data Drift Detection Results ===")
    print(f"Dataset drift detected: {data_drift_metrics['dataset_drift']}")
    print(f"Drift score: {data_drift_metrics['drift_score']:.4f}")
    print(f"Number of drifted features: {data_drift_metrics['number_of_drifted_columns']}")
    print(f"Number of features: {data_drift_metrics['number_of_columns']}")

    print("\n=== Target Drift Detection Results ===")
    print(f"Target drift detected: {target_drift_metrics['target_drift']}")
    print(f"Drift score: {target_drift_metrics['drift_score']:.4f}")

if __name__ == "__main__":
    main()