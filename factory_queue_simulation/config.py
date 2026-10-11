"""Default configuration for the factory queue simulation."""

DEFAULT_CONFIG = {
    "number_of_pathways": 10,
    "pathway_weights": [0.10] * 10,
    "total_workers": 350,
    "arrivals": 350,
    "arrival_start_time": "06:30",
    "arrival_end_time": "06:55",
    "morning_duration": 3600.0,
    "fingerprint_time_min": 8.0,
    "fingerprint_time_max": 14.0,
    "face_time_min": 10.0,
    "face_time_max": 18.0,
    "gate_time_min": 2.0,
    "gate_time_max": 5.0,
}