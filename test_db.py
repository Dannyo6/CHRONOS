import os
import sys

# Ensure UTF-8 stdout/stderr for Windows terminal output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# 1. Load environment variables with fallback defaults
load_dotenv()

host = os.getenv("INFLUX_URL", "http://localhost:8181")
token = os.getenv("INFLUX_TOKEN", "my-super-secret-auth-token")
org = os.getenv("INFLUX_ORG", "vitality")
bucket = os.getenv("INFLUX_DATABASE", "chronos_telemetry")

print("\n" + "=" * 50)
print(f"🔌 Connecting to InfluxDB at {host}...")
print(f"   Org: {org} | Bucket: {bucket}")
print("=" * 50)

client = None
try:
    # 2. Initialize InfluxDB v2 Client & Verify Health
    client = InfluxDBClient(url=host, token=token, org=org, timeout=5000)
    health = client.health()
    if health.status != "pass":
        print(f"⚠️ Health Check Warning: {health.status} ({health.message})")
    else:
        print(f"🟢 InfluxDB Service Health: {health.status.upper()}")

    # 3. Initialize Synchronous Write API
    write_api = client.write_api(write_options=SYNCHRONOUS)

    # 4. Create synthetic telemetry point
    test_point = (
        Point("vitality_metrics")
        .tag("device", "iot_simulator")
        .field("vitality_score", 99.5)
        .field("anomaly_detected", False)
    )

    # 5. Commit record to target bucket
    write_api.write(bucket=bucket, org=org, record=test_point)

    print("✅ SUCCESS: Authentication and write handshake verified.")
    print(f"✅ Data successfully written to bucket '{bucket}'.")
    print("=" * 50 + "\n")

except Exception as e:
    print(f"\n🔴 OFFLINE: InfluxDB verification failed.")
    print(f"Error Details: {e}\n")
    sys.exit(1)

finally:
    if client is not None:
        client.close()
        print("🔒 InfluxDB connection safely closed.")