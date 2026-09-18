```
 ██████╗██╗  ██╗██████╗  ██████╗ ███╗   ██╗ ██████╗ ███████╗
██╔════╝██║  ██║██╔══██╗██╔═══██╗████╗  ██║██╔═══██╗██╔════╝
██║     ███████║██████╔╝██║   ██║██╔██╗ ██║██║   ██║███████╗
██║     ██╔══██║██╔══██╗██║   ██║██║╚██╗██║██║   ██║╚════██║
╚██████╗██║  ██║██║  ██║╚██████╔╝██║ ╚████║╚██████╔╝███████║
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝
```
<div align="center">

### ⚡ *The Network EKG — An Agentless IoT Immune System* ⚡

*Checking the pulse. Not reading the mail.*

---

</div>




> **"Attackers can encrypt the payload. They can spoof the IP. They can randomize the packet size. But they cannot make their proxy process packets instantaneously. Physics always betrays them. Chronos catches the betrayal."**

---

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![PyTorch](https://img.shields.io/badge/PyTorch-CUDA-red?style=for-the-badge&logo=pytorch)
![Redis](https://img.shields.io/badge/Redis-Stream-orange?style=for-the-badge&logo=redis)
![InfluxDB](https://img.shields.io/badge/InfluxDB-2.7-purple?style=for-the-badge&logo=influxdb)
![Grafana](https://img.shields.io/badge/Grafana-Dashboard-yellow?style=for-the-badge&logo=grafana)
![Groq](https://img.shields.io/badge/Groq-LLaMA3-green?style=for-the-badge)
![eBPF](https://img.shields.io/badge/eBPF-Kernel--Space-black?style=for-the-badge&logo=linux)

</div>

---

## 🧬 The Core Concept

Current firewalls are like security guards reading everyone's mail *(Deep Packet Inspection)*. They violate privacy, consume excessive processing power for tiny IoT devices, and completely fail against zero-day exploits.

**Chronos does not read the mail. Chronos checks the pulse.**

By measuring the exact microseconds between network packets — the **Inter-Arrival Time (IAT)** — Chronos establishes a *Vitality Score* for every device on the network.

When a hacker intercepts traffic *(Man-in-the-Middle)* or floods the network *(DoS)*, they break the laws of physics. The timing delays. The heartbeat stutters. **Chronos catches the stutter, diagnoses the disease using AI, and autonomously amputates the attacker.**

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    UBUNTU EDGE DEVICE                           │
│                                                                 │
│   ┌──────────────────────────────────────────────────────┐     │
│   │  eBPF Kernel Probe (ebpf_edge.py)                    │     │
│   │  → Hooks into sys_enter_sendto() at kernel level     │     │
│   │  → Captures IAT with nanosecond precision            │     │
│   │  → Zero packet loss, zero userspace overhead         │     │
│   └──────────────────────┬───────────────────────────────┘     │
│                          │ TCP/IP (192.168.137.x)               │
└──────────────────────────┼──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    WINDOWS COMMAND CENTER                       │
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │    Redis    │───▶│   brain.py   │───▶│    InfluxDB      │   │
│  │   Stream    │    │  1D-CNN AE   │    │   Time Series    │   │
│  │ chronos:iat │    │  RTX 3050    │    │    Vitality      │   │
│  └─────────────┘    └──────┬───────┘    └────────┬─────────┘   │
│                            │                      │             │
│                     ┌──────▼───────┐    ┌────────▼─────────┐   │
│                     │   api.py     │    │     Grafana      │   │
│                     │  FastAPI +   │    │   SOC Dashboard  │   │
│                     │  Groq LLaMA3 │    │   localhost:3000 │   │
│                     └──────────────┘    └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔬 How It Works

### 1. The Sensor — eBPF Kernel Probe
A kernel-space C program injected via BCC hooks into every `sendto()` syscall on the edge device. It captures the **exact nanosecond timestamp** of each packet and computes the Inter-Arrival Time (IAT) delta — before any userspace software can touch the data.

```
IAT = timestamp_now - timestamp_last_packet (in nanoseconds)
```

This is pushed directly into a Redis Stream (`chronos:iat`).

### 2. The Nervous System — Redis Stream
An ultra-fast in-memory message broker buffers incoming IAT readings. The stream ensures zero packet loss even at 10,000+ packets/second, and allows the AI brain to consume data at its own pace.

### 3. The Brain — 1D-CNN Autoencoder (PyTorch)
The core anomaly detection engine:

```
Input Window : [iat_1, iat_2, ... iat_64]  → shape [1, 1, 64]
Encoder      : Conv1d → Conv1d → Bottleneck (compressed rhythm fingerprint)
Decoder      : ConvTranspose1d → ConvTranspose1d → Reconstruction
Loss         : E = MSE(x, x̂)  — Reconstruction Error
```

**Training Phase:**
- Collects 300+ windows of normal traffic
- Trains the autoencoder to reconstruct "normal" IAT rhythms
- Locks the **95th percentile reconstruction error** as the anomaly threshold

**Inference Phase:**
- Every 32 packets, a new window is fed to the model
- If `reconstruction_error > threshold` → **Vitality Score drops**
- If `vitality < 50%` → **ANOMALY DETECTED**

### 4. The Memory — InfluxDB 2.7
Every Vitality Score, reconstruction loss, XAI reasoning, and incident response command is written to InfluxDB as a time-series measurement. This powers the Grafana dashboard and provides full forensic audit trails.

### 5. The Detective — FastAPI + Groq LLaMA3
When an anomaly is detected, `brain.py` calls the XAI microservice which:
1. Packages the network physics data (vitality, loss, attacker IP)
2. Sends it to **Groq's LLaMA-3.3-70b** model
3. Receives a human-readable threat diagnosis AND a specific `iptables` firewall command
4. Writes both to InfluxDB for Grafana display

### 6. The Glass — Grafana SOC Dashboard
A real-time Security Operations Center UI showing:
- **Three Node Vitality Gauges** — green (secure) → red (compromised)
- **Live Temporal Rhythm EKG** — the network heartbeat
- **XAI Reasoning Panel** — plain-English threat diagnosis per node
- **Automated Incident Response** — live `iptables` firewall commands

---

## 🚀 Quick Start

### Prerequisites

**Windows (Command Center):**
```
Docker Desktop
Python 3.11+
NVIDIA GPU (RTX 3050 or better)
CUDA Toolkit
```

**Ubuntu (Edge Sensor):**
```
Linux Kernel 5.8+
BCC Tools
Python 3.11+
```

### Step 1 — Start the Stack (Windows)

```powershell
cd D:\Chronos-Enterprise
docker-compose up -d
```

Verify all containers are running:
```powershell
docker ps
# Should show: Redis, InfluxDB, Grafana — all Up
```

### Step 2 — Start the XAI Engine (Windows)

```powershell
$env:GROQ_API_KEY="your_groq_api_key_here"
uvicorn api:app --host 127.0.0.1 --port 5000
```

Get your free Groq API key at [console.groq.com](https://console.groq.com)

### Step 3 — Start the AI Brain (Windows)

```powershell
.\venv\Scripts\activate
python brain.py
```

The brain will automatically:
1. Collect 300 baseline IAT samples (calibration)
2. Train the 1D-CNN autoencoder
3. Lock the anomaly threshold
4. Begin live monitoring

### Step 4 — Start the eBPF Sensor (Ubuntu)

```bash
cd ~/Desktop
sudo python3 ebpf_edge.py --demo
```

The `--demo` flag automatically injects a MITM attack at T+60 seconds.

### Step 5 — Open the Dashboard

```
http://localhost:3000
```

Default credentials: `admin / admin`

---

## 📁 File Structure

```
Chronos-Enterprise/
│
├── brain.py              # 1D-CNN Autoencoder — core AI engine
├── api.py                # FastAPI + Groq LLM — XAI microservice
├── ebpf_edge.py          # eBPF kernel probe — edge sensor (Ubuntu)
├── iot_simulator.py      # IoT device simulator — testing/demo
├── docker-compose.yml    # Redis + InfluxDB + Grafana stack
│
├── venv/                 # Python virtual environment
└── README.md             # This file
```

---

## 🎯 Attack Signatures

| Attack Type | IAT Signature | Physics Explanation |
|---|---|---|
| **Normal** | μ=~1000ms, σ=~50ms | Steady MQTT keepalive rhythm |
| **MITM** | μ=~1400ms, σ=high | Proxy insertion adds ~400ms latency |
| **DoS Flood** | μ=~2ms, σ=low | Flood collapses inter-arrival to near-zero |
| **Jitter Attack** | Bimodal distribution | Re-routing causes chaotic timing |

---

## 🧠 What is Temporal Entropy?

**Temporal Entropy** measures the randomness in packet timing.

A healthy IoT device has a **low-entropy** heartbeat — packets arrive with predictable, consistent timing. An attacker performing MITM cannot avoid adding processing latency to every packet they intercept. This creates **high temporal entropy** — the rhythm becomes chaotic.

Chronos quantifies this chaos through reconstruction error:

```
Low Error  (< threshold) → Normal rhythm → Vitality: 99%  → SECURE
High Error (> threshold) → Broken rhythm → Vitality:  0%  → THREAT
```

---

## 🛡️ Why eBPF?

| Feature | Traditional DPI | Chronos eBPF |
|---|---|---|
| Payload inspection | ✅ Reads all content | ❌ Never touches payload |
| Privacy | ❌ Violates user privacy | ✅ Fully private |
| Zero-day detection | ❌ Signature-based only | ✅ Physics-based |
| Processing overhead | ❌ High CPU usage | ✅ Kernel-level, minimal overhead |
| Timestamp precision | ❌ Millisecond (userspace) | ✅ Nanosecond (kernel) |
| Packet loss | ❌ Possible under load | ✅ Zero — kernel ring buffer |

---

## 📊 Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| Edge Sensor | eBPF + BCC + Python | Kernel-space packet timing |
| Message Broker | Redis Streams | Zero-loss IAT buffering |
| AI Engine | PyTorch 1D-CNN | Anomaly detection |
| GPU Acceleration | NVIDIA RTX 3050 | Real-time inference |
| Time Series DB | InfluxDB 2.7 | Vitality score storage |
| XAI Gateway | FastAPI + Groq | LLM threat diagnosis |
| LLM Model | LLaMA-3.3-70b | Natural language reporting |
| Dashboard | Grafana | SOC visualization |
| Containerization | Docker Compose | Infrastructure orchestration |

---

## 🏆 🏆 Vision



Project Chronos represents a paradigm shift in network security:
- From **payload inspection** to **temporal physics analysis**
- From **signature-based detection** to **AI-powered anomaly detection**
- From **reactive response** to **autonomous threat neutralization**

---

## 👥 Team

**Team Vitality** — 2026

---

## 📄 License

MIT License — Built for Hackathon 2026

---

<div align="center">

**"The attacker cannot hide from physics."**

*⚡ Project Chronos — Checking the pulse, not reading the mail.*

</div>
