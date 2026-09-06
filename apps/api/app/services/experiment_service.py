"""
Experiment service for A/B testing and feature flagging.
"""
import hashlib
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..core import models
from ..core.repositories import experiment_repository
from ..core.exceptions import ExperimentNotFoundException
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ExperimentService:
    def __init__(self, db: Session):
        self.db = db
        self.experiment_repo = experiment_repository.ExperimentRepository(db)

    def get_experiment(self, experiment_id: str) -> Optional[models.Experiment]:
        """
        Get experiment by experiment_id.
        """
        logger.info(f"Fetching experiment {experiment_id}")
        return self.experiment_repo.get_experiment_by_id(experiment_id)

    def get_or_create_experiment(self, experiment_id: str, name: str, description: str = None,
                                config: Dict[str, Any] = None, metadata: Dict[str, Any] = None) -> models.Experiment:
        """
        Get an experiment by experiment_id or create it if it doesn't exist.
        """
        experiment = self.get_experiment(experiment_id)
        if experiment:
            return experiment

        # Create new experiment
        experiment_data = {
            "experiment_id": experiment_id,
            "name": name,
            "description": description,
            "config_": config or {},
            "metadata_": metadata or {}
        }
        experiment = models.Experiment(**experiment_data)
        return self.experiment_repo.create_experiment(experiment)

    def get_user_variant(self, experiment_id: str, user_id: int) -> Dict[str, Any]:
        """
        Get the variant assignment for a user in an experiment.
        Uses deterministic hashing for consistent assignment and stores the assignment.
        """
        # Get experiment details
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            raise ExperimentNotFoundException(f"Experiment {experiment_id} not found")

        # Check if user already has an assignment for this experiment
        existing_assignment = self.experiment_repo.get_experiment_assignment(experiment.id, user_id)
        if existing_assignment:
            logger.info(f"User {user_id} already assigned to {existing_assignment.variant} in experiment {experiment_id}")
            return {
                "experiment_id": experiment_id,
                "user_id": user_id,
                "variant": existing_assignment.variant,
                "model_version": existing_assignment.model_version,
                "assigned_at": existing_assignment.assigned_at,
                "metadata": existing_assignment.metadata_ or {}
            }

        # Create deterministic hash from experiment_id + user_id
        hash_input = f"{experiment_id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        # Get traffic allocation
        traffic_allocation = experiment.config_.get("traffic_allocation", {})
        if not traffic_allocation:
            # Default to 50/50 split if no config
            traffic_allocation = {"control": 0.5, "treatment": 0.5}

        variants = list(traffic_allocation.keys())
        allocations = list(traffic_allocation.values())

        # Normalize allocations to sum to 1.0
        total = sum(allocations)
        if total == 0:
            # Avoid division by zero
            normalized_allocations = [1.0 / len(variants)] * len(variants)
        else:
            normalized_allocations = [alloc / total for alloc in allocations]

        # Determine variant based on hash
        hash_normalized = (hash_value % 10000) / 10000.0  # 0.0 to 1.0

        cumulative = 0.0
        selected_variant = variants[-1]  # default to last variant
        for i, variant in enumerate(variants):
            cumulative += normalized_allocations[i]
            if hash_normalized < cumulative:
                selected_variant = variant
                break

        # Get variant details
        variant_details = experiment.config_.get("variants", {}).get(selected_variant, {})
        model_version = variant_details.get("model_version")

        # Create and store the assignment
        assignment = models.ExperimentAssignment(
            experiment_id=experiment.id,
            user_id=user_id,
            variant=selected_variant,
            model_version=model_version,
            metadata_={}
        )
        stored_assignment = self.experiment_repo.create_experiment_assignment(assignment)

        logger.info(f"User {user_id} assigned to {selected_variant} in experiment {experiment_id}")

        return {
            "experiment_id": experiment_id,
            "user_id": user_id,
            "variant": selected_variant,
            "model_version": model_version,
            "assigned_at": stored_assignment.assigned_at,
            "metadata": stored_assignment.metadata_ or {}
        }

    def track_experiment_exposure(self, experiment_id: str, user_id: int, variant: str, context: Dict[str, Any] = None):
        """
        Track that a user was exposed to an experiment variant.
        Stores the exposure in the database as an interaction event.
        """
        # Get experiment
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            logger.warning(f"Experiment {experiment_id} not found for exposure tracking")
            return None

        # Create exposure event as an interaction
        exposure_interaction = models.Interaction(
            user_id=user_id,
            event_type="experiment_exposure",
            context_=context or {},
            metadata_={
                "experiment_id": experiment_id,
                "variant": variant
            }
        )

        # We don't have a product_id for exposure events, so we'll leave it as NULL
        # In a real implementation, we might want to handle this differently

        self.db.add(exposure_interaction)
        self.db.commit()
        self.db.refresh(exposure_interaction)

        logger.info(f"Stored experiment exposure: experiment_id={experiment_id}, user_id={user_id}, variant={variant}")
        return exposure_interaction

    def track_experiment_outcome(self, experiment_id: str, user_id: int, variant: str, outcome_type: str,
                               value: float = None, context: Dict[str, Any] = None):
        """
        Track an outcome metric for an experiment variant.
        Stores the outcome in the database as an interaction event.
        outcome_type can be: ctr, conversion, revenue, ndcg, latency, etc.
        """
        # Get experiment
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            logger.warning(f"Experiment {experiment_id} not found for outcome tracking")
            return None

        # Create outcome event as an interaction
        outcome_interaction = models.Interaction(
            user_id=user_id,
            event_type="experiment_outcome",
            context_=context or {},
            metadata_={
                "experiment_id": experiment_id,
                "variant": variant,
                "outcome_type": outcome_type,
                "value": value
            }
        )

        # We don't have a product_id for outcome events, so we'll leave it as NULL
        # In a real implementation, we might want to handle this differently

        self.db.add(outcome_interaction)
        self.db.commit()
        self.db.refresh(outcome_interaction)

        logger.info(f"Stored experiment outcome: experiment_id={experiment_id}, user_id={user_id}, variant={variant}, outcome_type={outcome_type}, value={value}")
        return outcome_interaction

    def get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get aggregated results for an experiment.
        Queries the database for exposure and outcome events and computes statistics.
        """
        # Get experiment
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return {"error": f"No experiment found with ID {experiment_id}"}

        # Get all assignments for this experiment
        assignments = self.experiment_repo.get_experiment_assignments(experiment.id)

        # Group assignments by variant
        variant_assignments = {}
        for assignment in assignments:
            if assignment.variant not in variant_assignments:
                variant_assignments[assignment.variant] = []
            variant_assignments[assignment.variant].append(assignment.user_id)

        # Get exposure and outcome events for this experiment
        exposures = self.db.query(models.Interaction).filter(
            models.Interaction.event_type == "experiment_exposure",
            models.Interaction.metadata_.contains([{"experiment_id": experiment_id}])
        ).all()

        outcomes = self.db.query(models.Interaction).filter(
            models.Interaction.event_type == "experiment_outcome",
            models.Interaction.metadata_.contains([{"experiment_id": experiment_id}])
        ).all()

        # Process results by variant
        results = {
            "experiment_id": experiment_id,
            "status": experiment.status,
            "variants": {}
        }

        for variant, user_ids in variant_assignments.items():
            # Count unique users exposed to this variant
            exposed_users = set()
            for exposure in exposures:
                exp_metadata = exposure.metadata_ or {}
                if exp_metadata.get("experiment_id") == experiment_id and exp_metadata.get("variant") == variant:
                    exposed_users.add(exposure.user_id)

            # Count outcomes for this variant
            outcome_counts = {}
            outcome_values = {}
            for outcome in outcomes:
                out_metadata = outcome.metadata_ or {}
                if out_metadata.get("experiment_id") == experiment_id and out_metadata.get("variant") == variant:
                    outcome_type = out_metadata.get("outcome_type")
                    value = out_metadata.get("value")

                    if outcome_type not in outcome_counts:
                        outcome_counts[outcome_type] = 0
                        outcome_values[outcome_type] = []

                    outcome_counts[outcome_type] += 1
                    if value is not None:
                        outcome_values[outcome_type].append(value)

            # Calculate metrics
            metrics = {}
            for outcome_type, count in outcome_counts.items():
                if outcome_type in ["ctr", "conversion_rate"]:
                    # Rate metrics: outcomes / exposures
                    exposure_count = len([u for u in exposed_users if u in user_ids])  # Simplified
                    if exposure_count > 0:
                        metrics[outcome_type] = count / exposure_count
                    else:
                        metrics[outcome_type] = 0.0
                elif outcome_type in ["revenue_per_recommendation", "ndcg@10", "avg_latency_ms"]:
                    # Average metrics
                    values = outcome_values.get(outcome_type, [])
                    if values:
                        metrics[outcome_type] = sum(values) / len(values)
                    else:
                        metrics[outcome_type] = 0.0
                else:
                    # Count metrics
                    metrics[outcome_type] = count

            results["variants"][variant] = {
                "model_version": self._get_variant_model_version(experiment, variant),
                "users": len(user_ids),
                "exposures": len(exposed_users),
                "metrics": metrics
            }

        # Calculate statistical significance (simplified)
        results["statistical_significance"] = self._calculate_statistical_significance(results["variants"])

        return results

    def _get_variant_model_version(self, experiment: models.Experiment, variant: str) -> Optional[str]:
        """Get the model version for a variant from experiment config."""
        variants = experiment.config_.get("variants", {})
        variant_details = variants.get(variant, {})
        return variant_details.get("model_version")

    def _calculate_statistical_significance(self, variants: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate statistical significance for metrics between variants.
        This is a simplified implementation - in practice you'd use proper statistical tests.
        """
        significance = {}

        # Only calculate if we have exactly two variants (A/B test)
        if len(variants) == 2:
            variant_items = list(variants.items())
            control_key, control_data = variant_items[0]
            treatment_key, treatment_data = variant_items[1]

            metrics_to_check = ["ctr", "conversion_rate", "revenue_per_recommendation", "ndcg@10"]
            for metric in metrics_to_check:
                control_value = control_data.get("metrics", {}).get(metric, 0)
                treatment_value = treatment_data.get("metrics", {}).get(metric, 0)

                # Simple significance check: if difference is > 10% and both values are > 0
                if control_value > 0 and treatment_value > 0:
                    relative_diff = abs(treatment_value - control_value) / control_value
                    significant = relative_diff > 0.1  # 10% threshold
                else:
                    significant = False

                significance[metric] = {
                    "p_value": 0.05 if significant else 0.5,  # Simplified
                    "significant": significant
                }
        else:
            # Not enough variants for significance testing
            pass

        return significance

def get_experiment_service(db: Session = None) -> ExperimentService:
    """
    Factory function to get an experiment service instance.
    """
    if db is None:
        db = SessionLocal()
    try:
        return ExperimentService(db)
    finally:
        db.close()