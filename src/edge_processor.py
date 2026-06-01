"""
edge_processor.py
-----------------
Edge layer: sits between the sensor simulation and the cloud.
Responsibilities:
  1. Validate / clean incoming readings.
  2. Detect anomalies locally (threshold-based).
  3. Attach a severity label.
  4. Forward only flagged or sampled readings to the MQTT publisher.

This keeps cloud costs low and reduces bandwidth — a core
principle of real Industrial IoT (IIoT) edge architectures.
"""

import json
from typing import Optional

# ─── Thresholds (same as sensor_simulation, kept here explicitly) ─────────────
THRESHOLDS = {
    "vibration":   {"warning": 3.0,  "critical": 4.0},   # mm/s
    "temperature": {"warning": 65.0, "critical": 75.0},  # °C
    "load":        {"warning": 160.0,"critical": 180.0},  # kg
}

# Send every Nth normal reading to the cloud (sampling to reduce traffic)
NORMAL_SAMPLE_RATE = 5   # 1-in-5 normal readings get forwarded


def assess_severity(reading: dict) -> str:
    """
    Return 'critical', 'warning', or 'normal' based on sensor values.
    The worst individual sensor drives the overall label.
    """
    worst = "normal"

    checks = {
        "vibration":   reading.get("vibration",   0),
        "temperature": reading.get("temperature", 0),
        "load":        reading.get("load",         0),
    }

    for sensor, value in checks.items():
        critical_thresh = THRESHOLDS[sensor]["critical"]
        warning_thresh  = THRESHOLDS[sensor]["warning"]

        if value >= critical_thresh:
            return "critical"          # no need to check further
        elif value >= warning_thresh:
            worst = "warning"

    return worst


def validate(reading: dict) -> bool:
    """Basic sanity checks — reject obviously corrupt readings."""
    required_keys = {"machine_id", "timestamp", "vibration", "temperature", "load"}
    if not required_keys.issubset(reading.keys()):
        return False
    if not (0 <= reading["vibration"]   <= 20):
        return False
    if not (0 <= reading["temperature"] <= 150):
        return False
    if not (0 <= reading["load"]        <= 400):
        return False
    return True


def process_batch(readings: list, verbose: bool = True) -> list:
    """
    Process a list of raw sensor readings.

    Returns a filtered list of readings enriched with:
      - severity   : 'normal' | 'warning' | 'critical'
      - edge_flagged: True if this reading should be forwarded to cloud
    """
    processed   = []
    normal_count = 0

    for raw in readings:
        # 1. Validate
        if not validate(raw):
            print(f"  ✗ Invalid reading skipped: {raw}")
            continue

        # 2. Assess severity
        severity = assess_severity(raw)
        enriched = {**raw, "severity": severity}

        # 3. Decide whether to forward
        if severity in ("warning", "critical"):
            enriched["edge_flagged"] = True
        else:
            # Sample normal readings — don't send every one
            normal_count += 1
            enriched["edge_flagged"] = (normal_count % NORMAL_SAMPLE_RATE == 0)

        processed.append(enriched)

        if verbose:
            flag_icon = {"critical": "🔴", "warning": "🟡", "normal": "🟢"}[severity]
            fwd = "→ CLOUD" if enriched["edge_flagged"] else "  local"
            print(f"  {flag_icon} [{severity.upper():8s}] {raw['machine_id']} | {fwd}")

    forwarded = [r for r in processed if r["edge_flagged"]]

    print(f"\n  Edge summary: {len(readings)} readings in | "
          f"{len(processed)} valid | {len(forwarded)} forwarded to cloud\n")

    return forwarded


if __name__ == "__main__":
    # Load sample data produced by sensor_simulation.py
    with open("data/raw_sensor_data.json") as f:
        raw_data = json.load(f)

    print("=== Edge Processor ===\n")
    cloud_bound = process_batch(raw_data)

    with open("data/edge_processed.json", "w") as f:
        json.dump(cloud_bound, f, indent=2)

    print("Saved → data/edge_processed.json")
