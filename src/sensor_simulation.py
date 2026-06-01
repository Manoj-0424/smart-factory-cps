"""
sensor_simulation.py
--------------------
Simulates a conveyor belt system with three sensors:
  - Vibration sensor  (mm/s)
  - Temperature sensor (°C)
  - Load sensor        (kg)

Uses SimPy for discrete-event simulation.
Synthetic / imaginary data — for portfolio / demonstration purposes only.
"""

import simpy
import random
import json
import time
from datetime import datetime

# ─── Normal operating ranges ────────────────────────────────────────────────
VIBRATION_NORMAL  = (0.5, 2.5)   # mm/s
TEMPERATURE_NORMAL = (30.0, 60.0) # °C
LOAD_NORMAL        = (50.0, 150.0) # kg

# ─── Fault thresholds ────────────────────────────────────────────────────────
VIBRATION_FAULT   = 4.0   # mm/s  — above this → fault
TEMPERATURE_FAULT = 75.0  # °C    — above this → fault
LOAD_FAULT        = 180.0 # kg    — above this → fault

# ─── How often faults are injected (probability per reading) ─────────────────
FAULT_PROBABILITY = 0.08   # 8 % chance of a fault spike per tick


def generate_reading(sensor_type: str, inject_fault: bool = False) -> float:
    """Return one synthetic sensor reading."""
    if sensor_type == "vibration":
        base = random.uniform(*VIBRATION_NORMAL)
        return round(base * random.uniform(2.5, 3.5), 3) if inject_fault else round(base, 3)

    elif sensor_type == "temperature":
        base = random.uniform(*TEMPERATURE_NORMAL)
        return round(base + random.uniform(20, 30), 2) if inject_fault else round(base, 2)

    elif sensor_type == "load":
        base = random.uniform(*LOAD_NORMAL)
        return round(base + random.uniform(40, 60), 2) if inject_fault else round(base, 2)

    return 0.0


def conveyor_sensor(env: simpy.Environment,
                    machine_id: str,
                    interval: float,
                    readings: list):
    """
    SimPy process: every `interval` seconds, take one reading from
    all three sensors, package as JSON, and append to `readings`.
    """
    while True:
        fault_now = random.random() < FAULT_PROBABILITY

        payload = {
            "machine_id":  machine_id,
            "timestamp":   datetime.utcnow().isoformat() + "Z",
            "vibration":   generate_reading("vibration",   fault_now),
            "temperature": generate_reading("temperature", fault_now),
            "load":        generate_reading("load",        fault_now),
            "fault_injected": fault_now,   # ground-truth label (for testing)
        }

        readings.append(payload)
        print(f"[{payload['timestamp']}] {machine_id} | "
              f"vib={payload['vibration']} mm/s | "
              f"temp={payload['temperature']} °C | "
              f"load={payload['load']} kg"
              + (" ⚠ FAULT SPIKE" if fault_now else ""))

        yield env.timeout(interval)


def run_simulation(duration: int = 30,
                   interval: float = 1.0,
                   machines: list = None) -> list:
    """
    Run the SimPy simulation.

    Args:
        duration:  How many simulated seconds to run.
        interval:  Seconds between each sensor reading.
        machines:  List of machine IDs to simulate.

    Returns:
        List of sensor reading dicts.
    """
    if machines is None:
        machines = ["CONV-01", "CONV-02", "CONV-03"]

    env      = simpy.Environment()
    readings = []

    for machine_id in machines:
        env.process(conveyor_sensor(env, machine_id, interval, readings))

    print(f"\n{'='*60}")
    print(f"  Smart Factory CPS — Sensor Simulation")
    print(f"  Machines : {machines}")
    print(f"  Duration : {duration}s  |  Interval : {interval}s")
    print(f"{'='*60}\n")

    env.run(until=duration)

    print(f"\n✅ Simulation complete — {len(readings)} readings generated.\n")
    return readings


if __name__ == "__main__":
    data = run_simulation(duration=10, interval=1.0)

    # Save to file so edge_processor.py can consume it
    with open("data/raw_sensor_data.json", "w") as f:
        json.dump(data, f, indent=2)
    print("Saved → data/raw_sensor_data.json")
