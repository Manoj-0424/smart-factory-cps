"""
fault_detector.py
-----------------
Cloud-side fault detection and maintenance prediction.

In a real AWS deployment this logic would live inside an
AWS Lambda function triggered by an IoT Rule. For this
portfolio project it runs locally and simulates that same logic.

Logic:
  - Rule-based thresholds for immediate alerts.
  - Rolling-window trend detection (rising temperature / vibration).
  - Maintenance score (0–100) derived from combined sensor health.
  - Outputs a maintenance recommendation per machine.
"""

import json
from collections import defaultdict, deque
from datetime import datetime

# ─── Window for trend analysis ────────────────────────────────────────────────
WINDOW_SIZE = 5   # last N readings per machine

# ─── Maintenance score weights ────────────────────────────────────────────────
WEIGHTS = {"vibration": 0.4, "temperature": 0.35, "load": 0.25}

# ─── Thresholds (normalised 0–1 scale per sensor) ────────────────────────────
SENSOR_MAX = {"vibration": 6.0, "temperature": 100.0, "load": 220.0}


def normalise(value: float, sensor: str) -> float:
    """Map raw sensor value to 0–1 scale (1 = maximum stress)."""
    return min(value / SENSOR_MAX[sensor], 1.0)


def compute_health_score(reading: dict) -> float:
    """
    Return a health score from 0 (critical) to 100 (perfect).
    Weighted combination of normalised sensor stresses.
    """
    stress = sum(
        WEIGHTS[s] * normalise(reading[s], s)
        for s in WEIGHTS
    )
    return round((1 - stress) * 100, 1)


def detect_trend(window: deque, sensor: str) -> str:
    """
    Analyse recent readings for a rising trend.
    Returns 'rising', 'stable', or 'falling'.
    """
    if len(window) < 3:
        return "stable"

    values = [r[sensor] for r in window]
    diffs  = [values[i+1] - values[i] for i in range(len(values)-1)]
    avg_diff = sum(diffs) / len(diffs)

    if avg_diff > 0.5:
        return "rising"
    elif avg_diff < -0.5:
        return "falling"
    return "stable"


def recommend_action(health: float, trends: dict, severity: str) -> dict:
    """
    Produce a maintenance recommendation based on health score,
    trends, and severity label from the edge layer.
    """
    if severity == "critical" or health < 30:
        return {
            "action":   "IMMEDIATE SHUTDOWN",
            "priority": "P1",
            "message":  "Critical fault detected. Stop machine immediately and inspect.",
        }
    elif severity == "warning" or health < 60:
        rising = [s for s, t in trends.items() if t == "rising"]
        msg = "Schedule maintenance within 24 hours."
        if rising:
            msg += f" Rising trend on: {', '.join(rising)}."
        return {"action": "SCHEDULE MAINTENANCE", "priority": "P2", "message": msg}
    else:
        return {
            "action":   "MONITOR",
            "priority": "P3",
            "message":  "System operating normally. Continue scheduled monitoring.",
        }


class FaultDetector:
    """
    Stateful detector — maintains a rolling window per machine.
    Call process(reading) for each incoming cloud message.
    """

    def __init__(self):
        # deque per machine_id, max length = WINDOW_SIZE
        self.windows: dict[str, deque] = defaultdict(lambda: deque(maxlen=WINDOW_SIZE))
        self.alerts  = []

    def process(self, reading: dict) -> dict:
        machine_id = reading["machine_id"]
        window     = self.windows[machine_id]
        window.append(reading)

        health = compute_health_score(reading)
        trends = {s: detect_trend(window, s) for s in WEIGHTS}
        recommendation = recommend_action(health, trends, reading.get("severity", "normal"))

        result = {
            "machine_id":     machine_id,
            "timestamp":      reading["timestamp"],
            "health_score":   health,
            "severity":       reading.get("severity", "normal"),
            "trends":         trends,
            "recommendation": recommendation,
        }

        # Store P1/P2 alerts separately
        if recommendation["priority"] in ("P1", "P2"):
            self.alerts.append(result)

        return result

    def process_batch(self, readings: list, verbose: bool = True) -> list:
        print("=== Cloud Fault Detector ===\n")
        results = []
        for r in readings:
            res = self.process(r)
            results.append(res)
            if verbose:
                icon = {"P1": "🔴", "P2": "🟡", "P3": "🟢"}[res["recommendation"]["priority"]]
                print(f"  {icon} {res['machine_id']} | "
                      f"health={res['health_score']:5.1f} | "
                      f"{res['recommendation']['action']}")

        print(f"\n  Alerts raised: {len(self.alerts)} "
              f"(P1: {sum(1 for a in self.alerts if a['recommendation']['priority']=='P1')} | "
              f"P2: {sum(1 for a in self.alerts if a['recommendation']['priority']=='P2')})\n")
        return results


if __name__ == "__main__":
    with open("data/edge_processed.json") as f:
        readings = json.load(f)

    detector = FaultDetector()
    results  = detector.process_batch(readings)

    with open("data/fault_detection_results.json", "w") as f:
        json.dump(results, f, indent=2)

    with open("data/alerts.json", "w") as f:
        json.dump(detector.alerts, f, indent=2)

    print("Saved → data/fault_detection_results.json")
    print("Saved → data/alerts.json")
