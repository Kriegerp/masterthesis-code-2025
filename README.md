# masterthesis-code-2025

```markdown
# Smart Home Performance Benchmark Suite

This repository contains the source code and benchmark tools developed for my Master's Thesis: **"Performance Testing im Smart Home: Analyse von MQTT, HABApp und openHAB"** at *Furtwangen University (HFU)*.

## Overview

The goal of this project was to empirically analyze the performance limits of a typical open-source smart home architecture. A modular benchmark suite was developed to measure:
* Latency: Round-trip time (RTT) for MQTT, HABApp, and openHAB.
* Throughput: Maximum messages per second (msg/s).
* Stability: Long-term load tests (e.g., 5 minutes at constant load).
* Stress: System breaking points and packet loss analysis.

## System Architecture

The benchmark suite consists of a Python-based **Load Generator (Client)** and specific **Responder Rules (Server)** implemented in HABApp and openHAB.

* Language: Python 3.10+
* Communication: MQTT (via Eclipse Mosquitto)
* Middleware: HABApp, openHAB
* Library: `paho-mqtt`

## Usage

The main entry point is the `main.py` script. It supports various modes to test different components.

### 1. Throughput Test (Example)
To test the maximum throughput of the MQTT broker:
```bash
python3 main.py --mode mqtt_throughput --duration 60 --delay 0 --qos 0 --payload_size 200

```

### 2. Load Test (Stability)

To simulate a constant load over 5 minutes:

```bash
python3 main.py --mode habapp_loadtest --duration 300 --delay 0.05 --qos 1 --payload_size 200

```

### 3. Stress Test (Finding Limits)

To incrementally increase load until failure:

```bash
python3 main.py --mode openhab_stresstest --duration 60 --delay 0.01 --qos 0

```

## Repository Structure

* `src/`: Contains the source code for the benchmark client.
* `main.py`: CLI entry point for all tests.
* `utils.py`: Helper functions for payload generation and tracking.
* `modes/`: Specific implementation for each test scenario (Latency, Throughput, Stress).

## Requirements

* Python 3.x
* `paho-mqtt` library

Install dependencies via:

```bash
pip install paho-mqtt psutil

```

## 📄 License

This project is licensed under the MIT License

---

*Created by Patrick Krieger, 2025.*

```
