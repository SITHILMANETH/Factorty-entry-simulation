"""Baseline experiments for the factory queue simulation."""

from random import Random
from datetime import datetime

import pandas as pd

from .config import DEFAULT_CONFIG


def clock_to_seconds(value):
    """Convert an HH:MM clock value into seconds after midnight."""
    if isinstance(value, (int, float)):
        return float(value)
    return (
        datetime.strptime(str(value).strip(), "%H:%M")
        - datetime.strptime("00:00", "%H:%M")
    ).total_seconds()


def run_baseline_experiment(seed=None, animate=False, config=None):
    """Simulate morning arrivals through pathway authentication and spin gates."""
    del animate
    settings = dict(DEFAULT_CONFIG)
    if config:
        settings.update(config)

    random = Random(seed)
    arrival_start_seconds = clock_to_seconds(settings["arrival_start_time"])
    arrival_end_seconds = clock_to_seconds(settings["arrival_end_time"])
    arrival_window = arrival_end_seconds - arrival_start_seconds
    if arrival_window <= 0:
        raise ValueError("arrival_end_time must be later than arrival_start_time")
    pathway_available_at = [0.0] * settings["number_of_pathways"]
    worker_events = []
    pathway_metrics = []

    for job_id in range(settings["arrivals"]):
        arrival_time = random.betavariate(2.2, 5.0) * arrival_window
        pathway = random.choices(
            range(settings["number_of_pathways"]),
            weights=settings["pathway_weights"],
            k=1,
        )[0]
        auth_method = random.choice(("fingerprint", "face"))
        if auth_method == "fingerprint":
            auth_time = random.uniform(
                settings["fingerprint_time_min"],
                settings["fingerprint_time_max"],
            )
        else:
            auth_time = random.uniform(
                settings["face_time_min"], settings["face_time_max"]
            )
        gate_time = random.uniform(
            settings["gate_time_min"], settings["gate_time_max"]
        )
        auth_start = max(arrival_time, pathway_available_at[pathway])
        auth_end = auth_start + auth_time
        gate_start = auth_end
        gate_end = gate_start + gate_time
        pathway_available_at[pathway] = gate_end
        worker_events.append(
            {
                "job_id": job_id,
                "worker_id": job_id % settings["total_workers"],
                "pathway": pathway,
                "auth_method": auth_method,
                "arrival_time": arrival_time,
                "auth_start": auth_start,
                "auth_end": auth_end,
                "gate_start": gate_start,
                "gate_end": gate_end,
                "exit_time": gate_end,
                "wait_time": auth_start - arrival_time,
                "auth_time": auth_time,
                "gate_time": gate_time,
            }
        )

    events = pd.DataFrame(worker_events)
    for pathway, pathway_events in events.groupby("pathway"):
        pathway_metrics.append(
            {
                "pathway": pathway,
                "jobs": len(pathway_events),
                "average_wait_time": pathway_events["wait_time"].mean(),
                "average_auth_time": pathway_events["auth_time"].mean(),
                "average_gate_time": pathway_events["gate_time"].mean(),
                "average_service_time": (
                    pathway_events["auth_time"] + pathway_events["gate_time"]
                ).mean(),
                "throughput_time": pathway_events["exit_time"].max(),
                "peak_wait_time": pathway_events["wait_time"].max(),
            }
        )

    return {
        "metrics": pd.DataFrame(pathway_metrics),
        "worker_events": worker_events,
        "duration": events["exit_time"].max(),
        "arrival_start_seconds": arrival_start_seconds,
        "arrival_end_seconds": arrival_end_seconds,
    }