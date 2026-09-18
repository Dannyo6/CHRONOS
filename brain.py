"""
===================================================================
  PROJECT CHRONOS — AI INFERENCE ENGINE (SCALABLE FLEET BUILD)
===================================================================
"""
import time
import sys
import argparse
import numpy as np
import requests
import torch
import torch.nn as nn
from collections import deque
from datetime import datetime

try:
    import redis
except ImportError:
    print("⚠️ Please run: pip install redis")
    sys.exit(1)

try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUX_AVAILABLE = True
except ImportError:
    INFLUX_AVAILABLE = False

# --- CONFIGURATION ---
REDIS_HOST           = "localhost"
REDIS_PORT           = 6379

INFLUX_URL           = "http://localhost:8181"
INFLUX_TOKEN         = "my-super-secret-auth-token"
INFLUX_ORG           = "vitality"
INFLUX_BUCKET        = "chronos_telemetry"

# --- AI HYPERPARAMETERS ---
WINDOW_SIZE          = 64
WINDOW_STRIDE        = 32
MIN_CALIBRATION      = 300
TRAINING_EPOCHS      = 100
LEARNING_RATE        = 0.001

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --- 1D-CNN AUTOENCODER ---
class ChronosCNN(nn.Module):
    def __init__(self, window_size=WINDOW_SIZE):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv1d(1, 16, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm1d(16),
            nn.LeakyReLU(0.2),
            nn.Conv1d(16, 32, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm1d(32),
            nn.LeakyReLU(0.2),
            nn.Conv1d(32, 16, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm1d(16),
            nn.LeakyReLU(0.2),
        )

        with torch.no_grad():
            dummy = torch.zeros(1, 1, window_size)
            self._enc_size = self.encoder(dummy).numel()

        self.fc_enc = nn.Linear(self._enc_size, 8)
        self.fc_dec = nn.Linear(8, self._enc_size)

        self.decoder = nn.Sequential(
            nn.ConvTranspose1d(16, 32, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm1d(32),
            nn.LeakyReLU(0.2),
            nn.ConvTranspose1d(32, 16, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm1d(16),
            nn.LeakyReLU(0.2),
            nn.ConvTranspose1d(16, 1, kernel_size=4, stride=2, padding=1),
        )
        self.resize = nn.AdaptiveAvgPool1d(window_size)

    def forward(self, x):
        h = self.encoder(x)
        flat = h.view(h.size(0), -1)
        z = self.fc_enc(flat)
        h2 = self.fc_dec(z)
        spatial = self._enc_size // 16
        h2 = h2.view(h2.size(0), 16, spatial)
        out = self.decoder(h2)
        return self.resize(out)


def normalize_window(window):
    return np.log1p(window) / 10.0

def loss_to_vitality(loss, threshold):
    if threshold <= 0:
        return 100.0
    ratio = loss / threshold
    return float(np.clip(100.0 * (1.0 - ratio / 2.0), 0.0, 100.0))


class RedisReader:
    def __init__(self, stream_name):
        self.client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.stream_name = stream_name
        self.last_id = "$"
        try:
            self.client.ping()
            print(f"  ✅ Redis connected to stream: {self.stream_name}")
        except:
            print("❌ Redis not found.")
            sys.exit(1)

    def read_batch(self):
        result = self.client.xread({self.stream_name: self.last_id}, count=50, block=1000)
        entries = []
        if result:
            for _, messages in result:
                for msg_id, fields in messages:
                    self.last_id = msg_id
                    try:
                        entries.append({
                            "iat_ms": float(fields.get("iat_ms", 0)),
                            "device_id": fields.get("device_id", "unknown"),
                        })
                    except:
                        continue
        return entries


class InfluxWriter:
    def __init__(self):
        self.available = INFLUX_AVAILABLE
        if self.available:
            try:
                self.client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
                self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
                print("  ✅ InfluxDB connected at http://localhost:8181")
            except:
                self.available = False
                print("  ⚠️ InfluxDB unavailable")

    def write_vitality(self, vitality, loss, limit, is_anomaly,
                       dev_id, xai_message, incident_response):
        if not self.available:
            return
        try:
            point = (
                Point("vitality")
                .tag("device_id", dev_id)
                .field("vitality_score",      float(vitality))
                .field("reconstruction_loss", float(loss))
                .field("threshold",           float(limit))
                .field("is_anomaly",          bool(is_anomaly))
                .field("xai_reasoning",       str(xai_message))
                .field("incident_response",   str(incident_response))
                .time(datetime.utcnow(), WritePrecision.MS)
            )
            self.write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        except Exception as e:
            print(f"  ⚠️ DATABASE WRITE ERROR: {e}")


def main(target_device, redis_stream):
    print(f"\n🧠 PROJECT CHRONOS — AI ENGINE STABLE BUILD (TARGET: {target_device})")

    reader    = RedisReader(redis_stream)
    influx    = InfluxWriter()
    model     = ChronosCNN().to(DEVICE)
    criterion = nn.MSELoss()

    # PHASE 1: CALIBRATION
    print(f"\n📡 PHASE 1: CALIBRATION...")
    baseline_iats = []
    reader.client.delete(redis_stream)

    while len(baseline_iats) < MIN_CALIBRATION:
        for e in reader.read_batch():
            if e["iat_ms"] > 0:
                baseline_iats.append(e["iat_ms"])
        print(f"  Collected: {len(baseline_iats)}/{MIN_CALIBRATION}", end="\r")

    # PHASE 2: TRAINING
    print(f"\n⚙️  PHASE 2: TRAINING...")
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    windows = [
        normalize_window(np.sort(baseline_iats[i:i + WINDOW_SIZE]))
        for i in range(0, len(baseline_iats) - WINDOW_SIZE, WINDOW_STRIDE)
    ]
    X = torch.tensor(np.array(windows), dtype=torch.float32).unsqueeze(1).to(DEVICE)

    for epoch in range(TRAINING_EPOCHS):
        optimizer.zero_grad()
        loss = criterion(model(X), X)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        errors = nn.MSELoss(reduction='none')(model(X), X).mean(dim=[1, 2]).cpu().numpy()

    learned_limit = float(np.percentile(errors, 95)) * 2.0
    threshold = max(0.80, learned_limit)
    print(f"✅ Training Locked. Threshold: {threshold:.6f}")

    # PHASE 3: LIVE MONITORING
    print("\n🔴 PHASE 3: LIVE MONITORING ACTIVE")
    print(f"{'TIME':<12} {'VITALITY':>8} {'LOSS':>10}  STATUS")
    print("-" * 50)

    iat_buffer      = deque(maxlen=WINDOW_SIZE)
    vitality_smooth = deque(maxlen=5)
    packets_seen    = 0
    last_api_call   = 0
    
    # AI CONTENT CACHE (Ensures UI stability during packet floods)
    cached_xai      = "Anomaly detected: Timing jitter threshold exceeded (API Cooldown/Offline)"
    cached_incident = "iptables -A INPUT -s 192.168.1.105 -j DROP"

    try:
        while True:
            if reader.client.xlen(redis_stream) > 200:
                reader.client.xtrim(redis_stream, maxlen=50)
                reader.last_id = "$"  

            for e in reader.read_batch():
                if e["iat_ms"] <= 0:
                    continue

                iat_buffer.append(e["iat_ms"])
                packets_seen += 1

                if len(iat_buffer) == WINDOW_SIZE and packets_seen % WINDOW_STRIDE == 0:
                    window    = np.sort(np.array(iat_buffer))
                    normed    = normalize_window(window)
                    tensor_in = torch.tensor(normed, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(DEVICE)

                    with torch.no_grad():
                        loss = criterion(model(tensor_in), tensor_in).item()

                    vitality_smooth.append(loss_to_vitality(loss, threshold))
                    vitality   = float(np.median(vitality_smooth))
                    is_anomaly = vitality < 50.0

                    ts = datetime.now().strftime("%H:%M:%S")

                    # HEALTHY STATE
                    xai_message       = "Baseline Temporal Rhythm Matched. Confidence: High."
                    incident_response = "System Secure. No action required."

                    # ANOMALY STATE
                    if is_anomaly:
                        current_time = time.time()
                        
                        # Only ask Groq if cooldown has passed
                        if current_time - last_api_call > 5.0:
                            try:
                                res = requests.post(
                                    "http://127.0.0.1:5000/api/v1/analyze_threat",
                                    json={"vitality": vitality, "loss": loss},
                                    timeout=1.5
                                )
                                response_data     = res.json()
                                xai_message       = response_data.get("xai_reasoning")
                                incident_response = response_data.get("incident_response")
                                
                                # Update Cache
                                cached_xai      = xai_message
                                cached_incident = incident_response
                                last_api_call   = current_time
                            except (requests.exceptions.RequestException, Exception):
                                # FALLBACK: Edge failsafe defaults on API timeout or error
                                xai_message       = "Anomaly detected: Timing jitter threshold exceeded (API Cooldown/Offline)"
                                incident_response = "iptables -A INPUT -s 192.168.1.105 -j DROP"
                                cached_xai        = xai_message
                                cached_incident   = incident_response
                                last_api_call     = current_time
                        else:
                            # COOLDOWN: Use Cache to keep UI stable
                            xai_message       = cached_xai
                            incident_response = cached_incident

                    influx.write_vitality(
                        vitality, loss, threshold,
                        is_anomaly, target_device,
                        xai_message, incident_response
                    )

                    if is_anomaly:
                        print(f"{ts:<12} {vitality:>7.1f}% {loss:>10.4f}  🚨 THREAT: {xai_message}")
                    else:
                        print(f"{ts:<12} {vitality:>7.1f}% {loss:>10.4f}  ✔️  Normal")

    except KeyboardInterrupt:
        print("\n🛑 Chronos shutting down.")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chronos AI Engine Microservice")
    parser.add_argument("--device", type=str, default="edge_01", help="Device ID to monitor")
    args = parser.parse_args()
    
    stream_name = f"chronos:iat:{args.device}"
    main(target_device=args.device, redis_stream=stream_name)