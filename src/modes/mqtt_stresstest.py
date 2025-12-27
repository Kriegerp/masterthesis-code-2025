# modes/mqtt_stresstest.py
import time, threading, paho.mqtt.client as mqtt
from utils import generate_payload
from datetime import datetime
import os
import psutil   # ✅ Systemmonitoring

def run_mqtt_stresstest(args, BROKER_IP):
    results = []

    # --- Subscriber ---
    total_received = 0
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

    # Parameter: Start-Rate, Schrittweite, Dauer pro Stufe
    current_delay = args.delay       # Start-Delay zwischen Nachrichten
    step_factor = 0.5                # halbiert Delay pro Stufe (doppelt so schnell)
    stage_duration = args.duration   # Dauer pro Stufe in Sekunden

    stage = 0
    while current_delay > 0.0001:  # Abbruch, wenn Delay extrem klein
        stage += 1
        total_sent = 0
        total_received = 0
        start_time = time.time()

        # --- Monitoring pro Stufe ---
        cpu_samples = []
        ram_samples = []

        while time.time() - start_time < stage_duration:
            msg_id = f"stage{stage}_msg{total_sent}"
            payload = generate_payload(args.payload_size, msg_id)
            pub_client.publish(args.topic, payload, qos=args.qos)
            total_sent += 1
            if current_delay > 0:
                time.sleep(current_delay)

            # alle 5 Sekunden CPU/RAM loggen
            if total_sent % int(max(1, 5 / current_delay)) == 0:
                cpu_usage = psutil.cpu_percent(interval=None)
                ram_usage = psutil.virtual_memory().percent
                cpu_samples.append(cpu_usage)
                ram_samples.append(ram_usage)

        duration = time.time() - start_time
        send_rate = total_sent / duration if duration > 0 else 0
        recv_rate = total_received / duration if duration > 0 else 0
        loss_pct = (1 - (total_received / total_sent)) * 100 if total_sent > 0 else 0

        avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
        avg_ram = sum(ram_samples) / len(ram_samples) if ram_samples else 0

        print(f"\n📊 Stufe {stage}: Delay={current_delay:.6f}s")
        print(f"   Gesendet:   {total_sent} → {send_rate:.2f} msg/s")
        print(f"   Empfangen:  {total_received} → {recv_rate:.2f} msg/s")
        print(f"   Verlust:    {total_sent - total_received} ({loss_pct:.2f}%)")
        print(f"   CPU: {avg_cpu:.1f}% | RAM: {avg_ram:.1f}%")

        results.append({
            "Stufe": stage,
            "Delay": current_delay,
            "Gesendet": total_sent,
            "Empfangen": total_received,
            "Send-Rate": send_rate,
            "Recv-Rate": recv_rate,
            "Verlust%": loss_pct,
            "Dauer_s": duration,
            "CPU%": avg_cpu,
            "RAM%": avg_ram,
        })

        # Delay reduzieren → Rate erhöhen
        current_delay *= step_factor

    pub_client.loop_stop()
    sub_client.loop_stop()

    # --- Markdown-Tabelle speichern ---
    os.makedirs("latency_markdowns", exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_file = os.path.join("latency_markdowns", f"stresstest_qos{args.qos}_{timestamp_str}.md")

    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"# MQTT Stresstest QoS {args.qos}\n\n")
        f.write("| Stufe | Delay (s) | Gesendet | Empfangen | Send-Rate (msg/s) | Recv-Rate (msg/s) | Verlust% | CPU% | RAM% |\n")
        f.write("|-------|-----------|----------|-----------|-------------------|-------------------|----------|------|------|\n")
        for r in results:
            f.write(f"| {r['Stufe']} | {r['Delay']:.6f} | {r['Gesendet']} | {r['Empfangen']} | "
                    f"{r['Send-Rate']:.2f} | {r['Recv-Rate']:.2f} | {r['Verlust%']:.2f}% | "
                    f"{r['CPU%']:.1f} | {r['RAM%']:.1f} |\n")

    print(f"\n📝 Markdown-Tabelle gespeichert unter: {md_file}")