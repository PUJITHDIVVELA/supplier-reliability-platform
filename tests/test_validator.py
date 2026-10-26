"""
Tests for Audit Engine and Validation Rules.
"""
import pytest
from supplier_reliability.generator.pipeline import run_pipeline
from supplier_reliability.validator.audit_engine import AuditEngine
from supplier_reliability.config import DEFAULT_SEED


def test_validator_detects_all_anomalies_with_perfect_accuracy():
    """Validates that the AuditEngine achieves 100% precision and recall against ground truth."""
    dataset = run_pipeline(scale="starter", seed=DEFAULT_SEED, inject_anomalies=True)
    engine = AuditEngine(dataset)
    report = engine.run_all_validations()

    gt_eval = report.ground_truth_evaluation

    assert gt_eval["precision"] == 1.0
    assert gt_eval["recall"] == 1.0
    assert gt_eval["f1_score"] == 1.0
    assert gt_eval["false_positives"] == 0
    assert gt_eval["false_negatives"] == 0


def test_clean_baseline_has_zero_issues():
    """Validates that when inject_anomalies=False, no issues are flagged."""
    dataset = run_pipeline(scale="micro", seed=DEFAULT_SEED, inject_anomalies=False)
    engine = AuditEngine(dataset)
    report = engine.run_all_validations()

    assert report.total_issues_found == 0
    assert len(report.issues) == 0
