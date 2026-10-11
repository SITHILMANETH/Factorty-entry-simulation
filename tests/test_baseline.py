import pandas as pd

from factory_queue_simulation.config import DEFAULT_CONFIG
from factory_queue_simulation.experiments import run_baseline_experiment


def test_default_config_has_expected_pathways():
    assert DEFAULT_CONFIG["number_of_pathways"] == 10
    assert len(DEFAULT_CONFIG["pathway_weights"]) == 10
    assert DEFAULT_CONFIG["total_workers"] > 0


def test_run_baseline_experiment_returns_metrics_and_workers():
    result = run_baseline_experiment(seed=42, animate=False)

    assert "metrics" in result
    assert "worker_events" in result
    assert isinstance(result["metrics"], pd.DataFrame)
    assert len(result["worker_events"]) > 0
    assert result["metrics"].shape[0] > 0
