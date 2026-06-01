"""
mqtt_publisher.py
-----------------
Publishes processed sensor readings to AWS IoT Core via MQTT.

In a real deployment you would:
  - Use actual AWS IoT certificates (*.pem files).
  - Set ENDPOINT to your AWS IoT Core endpoint.

For this portfolio project, the publisher runs in DRY-RUN mode
by default (no real AWS connection needed) and prints exactly
what it would publish. Set DRY_RUN = False and fill in your
credentials to go live.

Dependencies:
  pip install awsiotsdk  (only needed when DRY_RUN = False)
"""

import json
import time
import os
from datetime import datetime

# ─── Configuration ─────────────────────────────────────────────────────────────
DRY_RUN  = True   # Set to False to publish to real AWS IoT Core

ENDPOINT = os.getenv("AWS_IOT_ENDPOINT", "YOUR_ENDPOINT.iot.ap-south-1.amazonaws.com")
CLIENT_ID  = "smart-factory-cps-edge-01"
TOPIC_BASE = "factory/conveyor"   # readings go to  factory/conveyor/<machine_id>

# Certificate paths (only used when DRY_RUN = False)
CERT_DIR     = "config/certs"
CA_CERT      = f"{CERT_DIR}/AmazonRootCA1.pem"
DEVICE_CERT  = f"{CERT_DIR}/device-certificate.pem.crt"
PRIVATE_KEY  = f"{CERT_DIR}/private.pem.key"

QOS = 1   # At-least-once delivery


# ─── Dry-run helper ─────────────────────────────────────────────────────────
class DryRunClient:
    """Mimics the AWS IoT SDK publish API without a real connection."""

    def __init__(self):
        print(f"[DRY-RUN] MQTT client initialised for endpoint: {ENDPOINT}")

    def publish(self, topic: str, payload: str, qos: int = 1):
        print(f"  📤 PUBLISH → {topic}")
        data = json.loads(payload)
        print(f"     severity={data.get('severity')} | "
              f"machine={data.get('machine_id')} | "
              f"vib={data.get('vibration')} | "
              f"temp={data.get('temperature')} | "
              f"load={data.get('load')}")


# ─── Real AWS IoT client (only imported when not dry-running) ────────────────
def _build_real_client():
    from awscrt import mqtt
    from awsiot import mqtt_connection_builder

    connection = mqtt_connection_builder.mtls_from_path(
        endpoint       = ENDPOINT,
        cert_filepath  = DEVICE_CERT,
        pri_key_filepath = PRIVATE_KEY,
        ca_filepath    = CA_CERT,
        client_id      = CLIENT_ID,
        clean_session  = False,
        keep_alive_secs = 30,
    )
    connect_future = connection.connect()
    connect_future.result()   # blocks until connected
    print(f"✅ Connected to AWS IoT Core at {ENDPOINT}")
    return connection


# ─── Publisher ───────────────────────────────────────────────────────────────
class MQTTPublisher:
    def __init__(self):
        self.client    = DryRunClient() if DRY_RUN else _build_real_client()
        self.published = 0
        self.failed    = 0

    def publish_reading(self, reading: dict):
        """Publish a single sensor reading to its machine-specific topic."""
        machine_id = reading.get("machine_id", "UNKNOWN")
        topic      = f"{TOPIC_BASE}/{machine_id}"

        # Add publish timestamp
        payload = {**reading, "published_at": datetime.utcnow().isoformat() + "Z"}

        try:
            self.client.publish(
                topic   = topic,
                payload = json.dumps(payload),
                qos     = QOS,
            )
            self.published += 1
        except Exception as e:
            print(f"  ❌ Publish failed for {machine_id}: {e}")
            self.failed += 1

    def publish_batch(self, readings: list, delay: float = 0.1):
        """Publish a list of readings with a small delay between each."""
        print(f"\n=== MQTT Publisher {'[DRY-RUN]' if DRY_RUN else '[LIVE]'} ===\n")
        for reading in readings:
            self.publish_reading(reading)
            time.sleep(delay)

        print(f"\n  ✅ Done — {self.published} published | {self.failed} failed\n")

    def disconnect(self):
        if not DRY_RUN:
            disconnect_future = self.client.disconnect()
            disconnect_future.result()
            print("Disconnected from AWS IoT Core.")


if __name__ == "__main__":
    # Load edge-processed data
    with open("data/edge_processed.json") as f:
        cloud_bound = json.load(f)

    publisher = MQTTPublisher()
    publisher.publish_batch(cloud_bound)
    publisher.disconnect()
