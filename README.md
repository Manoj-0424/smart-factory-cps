# 🏭 Cyber-Physical System for Smart Factory Predictive Maintenance

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![AWS IoT](https://img.shields.io/badge/AWS-IoT%20Core-orange?logo=amazonaws)
![MQTT](https://img.shields.io/badge/Protocol-MQTT-green)
![SimPy](https://img.shields.io/badge/Simulation-SimPy-lightgrey)
![License](https://img.shields.io/badge/License-MIT-blue)

A hands-on **Cyber-Physical System (CPS)** project that connects a simulated conveyor belt factory environment to the cloud for real-time **predictive maintenance**.

Sensor data is generated using **Python + SimPy**, processed at the **edge**, streamed to **AWS IoT Core via MQTT**, and analysed by a **cloud-side fault detection layer** that predicts maintenance needs before breakdowns occur.

> ⚠️ All sensor readings in this project are **synthetic / simulated** — generated programmatically for demonstration purposes.

---

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FACTORY FLOOR                            │
│                                                                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│   │ CONV-01  │    │ CONV-02  │    │ CONV-03  │  Conveyor Belts │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘                 │
│        │               │               │                        │
│        └───────────────┴───────────────┘                        │
│                        │                                        │
│               ┌─────────────────┐                               │
│               │ sensor_simulation│  Python + SimPy              │
│               │ vibration / temp │  Synthetic data              │
│               │ load readings    │                              │
│               └────────┬────────┘                              │
└────────────────────────┼────────────────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────────────────┐
│                   EDGE LAYER                                    │
│               ┌────────▼────────┐                               │
│               │  edge_processor │  Validate → Threshold check   │
│               │  Anomaly detect │  Severity label → Filter      │
│               └────────┬────────┘                               │
└────────────────────────┼────────────────────────────────────────┘
                         │  MQTT (QoS 1)
                         │  Topic: factory/conveyor/<machine_id>
┌────────────────────────┼────────────────────────────────────────┐
│                    AWS CLOUD                                    │
│               ┌────────▼────────┐                               │
│               │  AWS IoT Core   │  MQTT Broker                  │
│               └────────┬────────┘                               │
│                        │  IoT Rule → Lambda trigger             │
│               ┌────────▼────────┐                               │
│               │  fault_detector │  Health score + Trend analysis│
│               │  Maintenance    │  P1 / P2 / P3 alerts          │
│               │  Recommender    │                               │
│               └─────────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/Manoj-0424/smart-factory-cps.git
cd smart-factory-cps
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the full pipeline
```bash
python src/main.py
```

This runs in **dry-run mode** (no AWS account needed). You will see:
- Simulated sensor readings from 3 conveyor belts
- Edge filtering and anomaly detection
- Simulated MQTT publish logs
- Cloud fault detection results with health scores and alerts

---

## 📁 Project Structure

```
smart-factory-cps/
├── src/
│   ├── main.py                  # Entry point — runs full pipeline
│   ├── sensor_simulation.py     # SimPy-based sensor data generator
│   ├── edge_processor.py        # Edge anomaly detection & filtering
│   ├── mqtt_publisher.py        # MQTT publisher (dry-run + live)
│   └── fault_detector.py        # Cloud fault detection & health scoring
├── config/
│   └── certs/                   # AWS IoT certificates (gitignored)
├── docs/
│   └── aws_setup.md             # Step-by-step AWS IoT Core setup guide
├── data/                        # Generated at runtime (gitignored)
│   ├── raw_sensor_data.json
│   ├── edge_processed.json
│   ├── fault_detection_results.json
│   └── alerts.json
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🔬 How It Works

### Layer 1 — Sensor Simulation (`sensor_simulation.py`)
- Uses **SimPy** discrete-event simulation to model three conveyor belts running in parallel.
- Each machine emits **vibration** (mm/s), **temperature** (°C), and **load** (kg) readings every second.
- An 8% random fault injection rate creates realistic anomaly spikes for testing the detection pipeline.

### Layer 2 — Edge Processing (`edge_processor.py`)
- **Validates** readings (rejects corrupt or out-of-range data).
- **Labels** each reading: `normal` / `warning` / `critical` based on configurable thresholds.
- **Samples** normal readings (1-in-5) to reduce cloud traffic while forwarding all anomalies — a real IIoT bandwidth-saving pattern.

### Layer 3 — MQTT Publishing (`mqtt_publisher.py`)
- Publishes each cloud-bound reading to `factory/conveyor/<machine_id>` using **MQTT QoS 1**.
- Supports **dry-run mode** (default) and **live AWS IoT Core** mode (see `docs/aws_setup.md`).

### Layer 4 — Cloud Fault Detection (`fault_detector.py`)
- Computes a **health score (0–100)** from weighted sensor stresses.
- Analyses **rolling-window trends** (rising temperature = early warning).
- Issues prioritised recommendations:
  - 🔴 **P1 — Immediate Shutdown**: critical fault, stop machine now.
  - 🟡 **P2 — Schedule Maintenance**: warning trend, act within 24 hours.
  - 🟢 **P3 — Monitor**: healthy, continue normal operation.

---

## 📊 Sample Output

```
════════════════════════════════════════════════════════════
  SMART FACTORY CPS — PREDICTIVE MAINTENANCE PIPELINE
════════════════════════════════════════════════════════════

[1/4] Running sensor simulation …

  [2024-01-15T10:00:01Z] CONV-01 | vib=1.832 mm/s | temp=47.3 °C | load=112.4 kg
  [2024-01-15T10:00:01Z] CONV-02 | vib=5.241 mm/s | temp=81.2 °C | load=195.3 kg ⚠ FAULT SPIKE
  [2024-01-15T10:00:01Z] CONV-03 | vib=2.104 mm/s | temp=53.7 °C | load=98.6 kg

[2/4] Edge processor …

  🟢 [NORMAL  ] CONV-01  local
  🔴 [CRITICAL] CONV-02 → CLOUD
  🟢 [NORMAL  ] CONV-03  local

[4/4] Cloud fault detector …

  🔴 CONV-02 | health= 18.3 | IMMEDIATE SHUTDOWN
  🟢 CONV-01 | health= 74.6 | MONITOR
```

---

## ☁️ Deploying to AWS

See [`docs/aws_setup.md`](docs/aws_setup.md) for step-by-step instructions to:
- Create an AWS IoT Thing and certificates.
- Configure MQTT publishing to a real endpoint.
- Set up an IoT Rule to trigger a Lambda function.

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| Sensor simulation | Python 3, SimPy |
| Edge processing | Python 3 (pure stdlib) |
| IoT protocol | MQTT (QoS 1) |
| Cloud broker | AWS IoT Core |
| Fault detection | Python 3, rule-based + trend analysis |
| Infrastructure | AWS Lambda, IoT Rules (documented) |

---

## 📜 License

MIT — free to use, modify and share.

---

## 👤 Author

**Pandivaru Manoj Kumar**  
B.Tech Mechanical Engineering — Yogi Vemana University  
AWS Certified Solutions Architect – Associate  
📎 [GitHub](https://github.com/Manoj-0424) · [Medium](https://manoj-2404.medium.com/) · [Portfolio](https://manoj-cps.lovable.app/)
