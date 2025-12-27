# modes/habapp_throughput.py
import time, threading, paho.mqtt.client as mqtt
from utils import generate_payload
from datetime import datetime
import os
import psutil

def run_habapp_throughput(args, BROKER_IP):
    qos = getattr(args, "qos", 1)  # Standard: QoS 1
    print(f"\n🚀 Starte HABApp-Durchsatztest mit QoS {qos} …")

    total_sent = 0
    total_received = 0
    start_time = time.time()

    # --- Subscriber ---
    def on_message(client, userdata, msg):
        nonlocal total_received
        total_received += 1

    sub_client = mqtt.Client()
    sub_client.on_message = on_message
    sub_client.connect(BROKER_IP, 1883)
    sub_client.subscribe("/throughput/habapp/response", qos=qos)

    def sub_loop():
        sub_client.loop_forever()

    sub_thread = threading.Thread(target=sub_loop, daemon=True)
    sub_thread.start()

    # --- Publisher ---
    pub_client = mqtt.Client()
    pub_client.connect(BROKER_IP, 1883)
    pub_client.loop_start()

    # --- Monitoring ---
    cpu_samples = []
    ram_samples = []

    while time.time() - start_time < args.duration * 60:
        msg_id = f"habapp_qos{qos}_msg{total_sent}"
        payload = generate_payload(args.payload_size, msg_id)
        info = pub_client.publish("/throughput/habapp/input", payload, qos=qos)
        if qos > 0:
            info.wait_for_publish()

        total_sent += 1
        if args.delay > 0:
            time.sleep(args.delay)

        # alle ~5 Sekunden CPU/RAM loggen
        if total_sent % int(max(1, 5 / max(args.delay, 0.001))) == 0:
            cpu_usage = psutil.cpu_percent(interval=None)
            ram_usage = psutil.virtual_memory().percent
            cpu_samples.append(cpu_usage)
            ram_samples.append(ram_usage)

    pub_client.loop_stop()
    sub_client.loop_stop()

    duration = time.time() - start_time
    send_rate = total_sent / duration if duration > 0 else 0
    recv_rate = total_received / duration if duration > 0 else 0
    loss_pct = (1 - (total_received / total_sent)) * 100 if total_sent > 0 else 0

    avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    avg_ram = sum(ram_samples) / len(ram_samples) if ram_samples else 0

    print(f"\n📊 QoS {qos} abgeschlossen:")
    print(f"   Gesendet:   {total_sent} → {send_rate:.2f} msg/s")
    print(f"   Empfangen:  {total_received} → {recv_rate:.2f} msg/s")
    print(f"   Verlust:    {total_sent - total_received} ({loss_pct:.2f}%)")
    print(f"   CPU: {avg_cpu:.1f}% | RAM: {avg_ram:.1f}%")

    # --- Markdown speichern ---
    os.makedirs("latency_markdowns", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_file = os.path.join("latency_markdowns", f"habapp_throughput_qos{qos}_{ts}.md")

    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"# HABApp Durchsatztest QoS {qos}\n\n")
        f.write(f"- Dauer: {duration:.2f} s\n")
        f.write(f"- Gesendet: {total_sent}\n")
        f.write(f"- Empfangen: {total_received}\n")
        f.write(f"- Send-Rate: {send_rate:.2f} msg/s\n")
        f.write(f"- Empfangsrate: {recv_rate:.2f} msg/s\n")
        f.write(f"- Verlustquote: {loss_pct:.2f}%\n")
        f.write(f"- CPU%: {avg_cpu:.1f}\n")
        f.write(f"- RAM%: {avg_ram:.1f}\n")

    print(f"\n📝 HABApp-Durchsatztest gespeichert unter: {md_file}")

    return {
        "QoS": qos,
        "Gesendet": total_sent,
        "Empfangen": total_received,
        "Send-Rate": send_rate,
        "Recv-Rate": recv_rate,
        "Verlust%": loss_pct,
        "Dauer_s": duration,
        "CPU%": avg_cpu,
        "RAM%": avg_ram,
    }