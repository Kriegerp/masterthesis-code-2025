import time, threading, paho.mqtt.client as mqtt
from utils import generate_payload
from datetime import datetime
import os
import psutil

def run_openhab_stresstest(args, BROKER_IP):
    results = []

    qos = getattr(args, "qos", 1)  # Standard: QoS 1, kann über CLI gesetzt werden
    print(f"\n🚀 Starte openHAB-Stresstest mit QoS {qos} …")

    # --- Subscriber ---
    total_received = 0
    def on_message(client, userdata, msg):
        nonlocal total_received
        total_received += 1

    sub_client = mqtt.Client(clean_session=True)
    sub_client.on_message = on_message
    sub_client.connect(BROKER_IP, 1883)
    sub_client.subscribe("/stresstest/openhab/response", qos=qos)

    threading.Thread(target=sub_client.loop_forever, daemon=True).start()

    # --- Publisher ---
    pub_client = mqtt.Client(clean_session=True)
    pub_client.connect(BROKER_IP, 1883)
    pub_client.loop_start()

    # --- Stresstest ---
    current_delay = args.delay       # Start-Delay
    step_factor = 0.5                # halbiert Delay pro Stufe
    stage_duration = args.duration   # Dauer pro Stufe in Sekunden
    stage = 0

    while current_delay > 0.0001:  # Abbruchbedingung
        stage += 1
        total_sent = 0
        total_received = 0  # Reset pro Stufe
        start_time = time.time()

        # --- Monitoring pro Stufe ---
        cpu_samples = []
        ram_samples = []

        while time.time() - start_time < stage_duration:
            msg_id = f"openhab_qos{qos}_stage{stage}_msg{total_sent}"
            payload = generate_payload(args.payload_size, msg_id)
            pub_client.publish("/stresstest/openhab/command", payload, qos=qos)
            total_sent += 1
            if current_delay > 0:
                time.sleep(current_delay)

            # alle ~5 Sekunden CPU/RAM loggen
            if total_sent % int(max(1, 5 / current_delay)) == 0:
                cpu_usage = psutil.cpu_percent(interval=None)
                ram_usage = psutil.virtual_memory().percent
                cpu_samples.append(cpu_usage)
                ram_samples.append(ram_usage)

        duration = time.time() - start_time
        stage_received = total_received  # direkt gezählt in dieser Stufe

        send_rate = total_sent / duration if duration > 0 else 0
        recv_rate = stage_received / duration if duration > 0 else 0
        loss_pct = (1 - (stage_received / total_sent)) * 100 if total_sent > 0 else 0

        avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
        avg_ram = sum(ram_samples) / len(ram_samples) if ram_samples else 0

        print(f"\n📊 QoS{qos} – Stufe {stage}: Delay={current_delay:.6f}s")
        print(f"   Gesendet:   {total_sent} → {send_rate:.2f} msg/s")
        print(f"   Empfangen:  {stage_received} → {recv_rate:.2f} msg/s")
        print(f"   Verlust:    {total_sent - stage_received} ({loss_pct:.2f}%)")
        print(f"   CPU: {avg_cpu:.1f}% | RAM: {avg_ram:.1f}%")

        results.append({
            "QoS": qos,
            "Stufe": stage,
            "Delay": current_delay,
            "Gesendet": total_sent,
            "Empfangen": stage_received,
            "Send-Rate": send_rate,
            "Recv-Rate": recv_rate,
            "Verlust%": loss_pct,
            "Dauer_s": duration,
            "CPU%": avg_cpu,
            "RAM%": avg_ram,
        })

        current_delay *= step_factor

    pub_client.loop_stop()
    sub_client.loop_stop()

    # --- Markdown speichern ---
    os.makedirs("latency_markdowns", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_file = os.path.join("latency_markdowns", f"openhab_stresstest_qos{qos}_{ts}.md")

    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"# openHAB Stresstest QoS {qos}\n\n")
        f.write("| Stufe | Delay (s) | Gesendet | Empfangen | Send-Rate (msg/s) | Empfangsrate (msg/s) | Verlust% | CPU% | RAM% |\n")
        f.write("|-------|-----------|----------|-----------|-------------------|----------------------|----------|------|------|\n")
        for r in results:
            f.write(f"| {r['Stufe']} | {r['Delay']:.6f} | {r['Gesendet']} | {r['Empfangen']} | "
                    f"{r['Send-Rate']:.2f} | {r['Recv-Rate']:.2f} | {r['Verlust%']:.2f}% | "
                    f"{r['CPU%']:.1f} | {r['RAM%']:.1f} |\n")

    print(f"\n📝 openHAB-Stresstest gespeichert unter: {md_file}")
    return results