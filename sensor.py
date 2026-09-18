import argparse
import random
import sys
import time

# Ensure UTF-8 stdout/stderr for Windows terminal output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import redis

def parse_args():
    parser = argparse.ArgumentParser(description="Chronos Telemetry Edge Sensor Simulator")
    parser.add_argument("--device", type=str, default="edge_01", help="Device identifier (default: edge_01)")
    parser.add_argument("--host", type=str, default="localhost", help="Redis host (default: localhost)")
    parser.add_argument("--port", type=int, default=6379, help="Redis port (default: 6379)")
    return parser.parse_args()

def main():
    args = parse_args()
    stream_key = f"chronos:iat:{args.device}"

    print("\n" + "=" * 55)
    print(f"🛰️  PROJECT CHRONOS — TELEMETRY INGESTION PROBE")
    print(f"   Target Stream: {stream_key}")
    print(f"   Broker:        {args.host}:{args.port}")
    print("=" * 55 + "\n")

    try:
        r = redis.Redis(host=args.host, port=args.port, decode_responses=True)
        if not r.ping():
            print("🔴 REDIS INFRASTRUCTURE OFFLINE: Ping failed.")
            sys.exit(1)
        print("🟢 REDIS INFRASTRUCTURE: ONLINE")
        print(f"📡 Emitting continuous Gaussian telemetry to '{stream_key}' (Ctrl+C to stop)...")
    except redis.exceptions.ConnectionError as e:
        print(f"🔴 CONNECTION FAILED: Unable to reach Redis at {args.host}:{args.port} ({e})")
        sys.exit(1)
    except Exception as e:
        print(f"🔴 UNEXPECTED ERROR: {e}")
        sys.exit(1)

    packet_count = 0
    try:
        while True:
            # Gaussian distribution centered at ~50ms with jitter, clamped > 0.1ms
            iat_val = max(0.1, random.gauss(50.0, 2.5))
            payload = {
                "iat_ms": str(round(iat_val, 4)),
                "device_id": args.device
            }
            r.xadd(stream_key, payload)
            packet_count += 1
            if packet_count % 50 == 0:
                print(f"  [Transmitted: {packet_count} packets] Latest IAT: {payload['iat_ms']} ms", end="\r")
            time.sleep(0.02)
    except KeyboardInterrupt:
        print(f"\n🛑 Sensor stopped by user. Total packets emitted: {packet_count}")
    except redis.exceptions.ConnectionError as e:
        print(f"\n🔴 REDIS CONNECTION LOST: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n🔴 RUNTIME ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()