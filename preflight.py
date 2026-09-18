import socket
import urllib.request
import urllib.error
import redis
import time
import http.client
import sys

# Ensure UTF-8 stdout/stderr for Windows terminal output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# --- System Target Configuration ---
SERVICES = {
    "Redis (Stream Broker)": {"type": "redis", "host": "localhost", "port": 6379},
    "InfluxDB 3 (Time-Series Core)": {"type": "http", "url": "http://localhost:8181/health"},
    "Grafana (Visualization UI)": {"type": "http", "url": "http://localhost:3000/api/health"}
}

def print_status(service, is_online, details=""):
    if is_online:
        print(f"  [🟢 ONLINE]  {service.ljust(30)} {details}")
    else:
        print(f"  [🔴 OFFLINE] {service.ljust(30)} {details}")

def run_diagnostics():
    print("\n" + "="*50)
    print("🚀 CHRONOS ENTERPRISE: PREFLIGHT DIAGNOSTICS")
    print("="*50 + "\n")
    
    all_clear = True
    
    for name, config in SERVICES.items():
        try:
            if config["type"] == "redis":
                r = redis.Redis(host=config["host"], port=config["port"], socket_timeout=2)
                if r.ping():
                    print_status(name, True, f"(Port {config['port']})")
                else:
                    print_status(name, False, "(Ping Failed)")
                    all_clear = False
                    
            elif config["type"] == "http":
                req = urllib.request.Request(config["url"], method="GET")
                try:
                    with urllib.request.urlopen(req, timeout=2) as response:
                        if response.status in [200, 202, 204]:
                            print_status(name, True, f"(HTTP {response.status})")
                        else:
                            print_status(name, False, f"(HTTP {response.status})")
                            all_clear = False
                except urllib.error.HTTPError as e:
                    # If InfluxDB bounces us for missing a token, it means it is ONLINE and SECURE.
                    if e.code == 401: 
                        print_status(name, True, "(Secured / HTTP 401)")
                    else:
                        raise e # Pass to outer exception block
                        
        except (socket.timeout, urllib.error.URLError, redis.exceptions.ConnectionError, redis.exceptions.TimeoutError, http.client.RemoteDisconnected, ConnectionResetError) as e:
            print_status(name, False, "(Connection Refused)")
            all_clear = False

    print("\n" + "="*50)
    if all_clear:
        print("✅ SYSTEM READY: ALL VITAL INFRASTRUCTURE SECURE.")
    else:
        print("⚠️ WARNING: CRITICAL INFRASTRUCTURE DOWN. CHECK DOCKER.")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_diagnostics()