import time, threading, paho.mqtt.client as mqtt
from utils import generate_payload
from datetime import datetime
import os
import psutil  

def run_mqtt_loadtest(args, BROKER_IP):
    total_sent = 0
    total_received = 0

    # --- Subscriber ---
    def on_message(client, userdata, msg):
        nonlocal total_received
        total_received += 1

    sub_client = mqtt.Client()
    sub_client.on_message = on_message
    sub_client.connect(BROKER_IP, 1883)
    sub_client.subscribe(args.topic, qos=args.qos)

    def sub_loop():
        sub_client.loop_forever()

    sub_thread = threading.Thread(target=sub_loop, daemon=True)
    sub_thread.start()

    # --- Publisher ---
    pub_client = mqtt.Client()
    pub_client.connect(BROKER_IP, 1883)
    pub_client.loop_start()

    delay = args.delay
    start_time = time.time()

    # --- Monitoring Zeitreihe ---
    cpu_series = []
    ram_series = []
    timestamps = []

    next_sample = start_time + 60  # erste Minute

    while time.time() - start_time < args.duration:
        msg_id = f"loadtest_msg{total_sent}"
        payload = generate_payload(args.payload_size, msg_id)
        pub_client.publish(args.topic, payload, qos=args.qos)
        total_sent += 1

        if delay > 0:
            time.sleep(delay)

        # alle 60 Sekunden CPU/RAM loggen
        if time.time() >= next_sample:
            cpu_usage = psutil.cpu_percent(interval=None)
            ram_usage = psutil.virtual_memory().percent
            cpu_series.append(cpu_usage)
            ram_series.append(ram_usage)
            timestamps.append(int((time.time() - start_time) // 60))  # Minuten seit Start
            print(f"[Monitoring] Minute {timestamps[-1]}: CPU={cpu_usage:.1f}% | RAM={ram_usage:.1f}%")
            next_sample += 60

    duration = time.time() - start_time
    send_rate = total_sent / duration if duration > 0 else 0
    recv_rate = total_received / duration if duration > 0 else 0
    loss_pct = (1 - (total_received / total_sent)) * 100 if total_sent > 0 else 0

    pub_client.loop_stop()
    sub_client.loop_stop()

    # --- Markdown speichern ---
    os.makedirs("latency_markdowns", exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_file = os.path.join("latency_markdowns", f"loadtest_qos{args.qos}_{timestamp_str}.md")

    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"# MQTT Lasttest QoS {args.qos}\n\n")
        f.write(f"- Dauer: {duration:.2f} s\n")
        f.write(f"- Gesendet: {total_sent}\n")
        f.write(f"- Empfangen: {total_received}\n")
        f.write(f"- Send-Rate: {send_rate:.2f} msg/s\n")
        f.write(f"- Empfangsrate: {recv_rate:.2f} msg/s\n")
        f.write(f"- Verlustquote: {loss_pct:.2f}%\n\n")

        f.write("## Systemmonitoring pro Minute\n\n")
        f.write("| Minute | CPU% | RAM% |\n")
        f.write("|--------|------|------|\n")
        for i, cpu in enumerate(cpu_series):
            f.write(f"| {timestamps[i]} | {cpu:.1f} | {ram_series[i]:.1f} |\n")

    print(f"\n📝 Lasttest-Ergebnisse gespeichert unter: {md_file}")