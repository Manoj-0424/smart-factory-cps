"""
main.py
-------
Entry point — runs the full CPS pipeline end-to-end:

  1. Sensor simulation  (sensor_simulation.py)
  2. Edge processing    (edge_processor.py)
  3. MQTT publishing    (mqtt_publisher.py)
  4. Cloud fault detect (fault_detector.py)

Run:
    python src/main.py
"""

import json
import os
import sys

# Allow imports from src/
sys.path.insert(0, os.path.dirname(__file__))

from sensor_simulation import run_simulation
from edge_processor     import process_batch
from mqtt_publisher     import MQTTPublisher
from fault_detector     import FaultDetector


def main():
    os.makedirs("data", exist_ok=True)

    print("\n" + "═"*60)
    print("  SMART FACTORY CPS — PREDICTIVE MAINTENANCE PIPELINE")
    print("═"*60)

    # ── Step 1: Simulate sensors ─────────────────────────────────
    print("\n[1/4] Running sensor simulation …\n")
    raw_readings = run_simulation(
        duration = 20,
        interval = 1.0,
        machines = ["CONV-01", "CONV-02", "CONV-03"],
    )
    with open("data/raw_sensor_data.json", "w") as f:
        json.dump(raw_readings, f, indent=2)
    print(f"      → {len(raw_readings)} raw readings saved to data/raw_sensor_data.json")

    # ── Step 2: Edge processing ──────────────────────────────────
    print("\n[2/4] Running edge processor …\n")
    cloud_bound = process_batch(raw_readings, verbose=True)
    with open("data/edge_processed.json", "w") as f:
        json.dump(cloud_bound, f, indent=2)
    print(f"      → {len(cloud_bound)} readings forwarded to cloud layer")

    # ── Step 3: MQTT publish ─────────────────────────────────────
    print("\n[3/4] Publishing to AWS IoT Core (dry-run) …")
    publisher = MQTTPublisher()
    publisher.publish_batch(cloud_bound, delay=0.0)   # no delay in demo
    publisher.disconnect()

    # ── Step 4: Cloud fault detection ────────────────────────────
    print("\n[4/4] Running cloud fault detector …\n")
    detector = FaultDetector()
    results  = detector.process_batch(cloud_bound, verbose=True)

    with open("data/fault_detection_results.json", "w") as f:
        json.dump(results, f, indent=2)
    with open("data/alerts.json", "w") as f:
        json.dump(detector.alerts, f, indent=2)

    # ── Summary ──────────────────────────────────────────────────
    print("\n" + "═"*60)
    print("  PIPELINE COMPLETE")
    print("═"*60)
    print(f"  Raw readings       : {len(raw_readings)}")
    print(f"  Forwarded to cloud : {len(cloud_bound)}")
    print(f"  Total alerts       : {len(detector.alerts)}")
    print(f"\n  Output files in ./data/")
    print("    raw_sensor_data.json")
    print("    edge_processed.json")
    print("    fault_detection_results.json")
    print("    alerts.json")
    print("═"*60 + "\n")


if __name__ == "__main__":
    main()
