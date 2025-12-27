import time, threading, paho.mqtt.client as mqtt
from utils import generate_payload
from datetime import datetime
import os
import psutil

def run_habapp_loadtest(args, BROKER_IP):
    total_sent = 0
    total_received = 0
    interval = getattr(args, "interval", 10)  # Standard: alle 10 Sekunden Zwischenwerte
    qos = getattr(args, "qos", 1)             # Standard QoS 1

    # --- Subscriber ---
    def on_message(client, userdata, msg):
        nonlocal total_received
        total_received += 1

    sub_client = mqtt.Client(clean_session=True)
    sub_client.on_message = on_message
    sub_client.connect(BROKER_IP, 1883)
    sub_client.subscribe("/loadtest/habapp/response", qos=qos)

    def sub_loop():
        sub_client.loop_forever()

    sub_thread = threading.Thread(target=sub_loop, daemon=True)
    sub_thread.start()

    # --- Publisher ---
    pub_client = mqtt.Client(clean_session=True)
    pub_client.connect(BROKER_IP, 1883)
    pub_client.loop_start()

    delay = args.delay
    start_time = time.time()
    next_report = start_time + interval
    next_monitor = start_time + 60   # erste Minute

    # Ergebnisse für Zwischenwerte
    timeline = []
    cpu_series = []
    ram_series = []
    timestamps = []

    while time.time() - start_time < args.duration:
        msg_id = f"habapp_loadtest_msg{total_sent}"
        payload = generate_payload(args.payload_size, msg_id)

        # Publish mit ACK-Wartezeit
        info = pub_client.publish("/loadtest/habapp/input", payload, qos=qos)
        info.wait_for_publish()   # blockiert bis Broker bestätigt hat

        total_sent += 1
        if delay > 0:
            time.sleep(delay)

        now = time.time()

        # Zwischenwerte alle `interval` Sekunden
        if now >= next_report:
            elapsed = now - start_time
            send_rate = total_sent / elapsed if elapsed > 0 else 0
            recv_rate = total_received / elapsed if elapsed > 0 else 0
            loss_pct = (1 - (total_received / total_sent)) * 100 if total_sent > 0 else 0

            print(f"⏱ Zwischenstand nach {elapsed:.1f}s: "
                  f"Gesendet={total_sent}, Empfangen={total_received}, "
                  f"Verlust={loss_pct:.2f}%")

            timeline.append({
                "Zeit_s": round(elapsed, 1),
                "Gesendet": total_sent,
                "Empfangen": total_received,
                "Send-Rate": send_rate,
                "Recv-Rate": recv_rate,
                "Verlust%": loss_pct,
            })

            next_report += interval

        # Systemmonitoring pro Minute
        if now >= next_monitor:
            cpu_usage = psutil.cpu_percent(interval=None)
            ram_usage = psutil.virtual_memory().percent
            cpu_series.append(cpu_usage)
            ram_series.append(ram_usage)
            timestamps.append(int((now - start_time) // 60))
            print(f"[Monitoring] Minute {timestamps[-1]}: CPU={cpu_usage:.1f}% | RAM={ram_usage:.1f}%")
            next_monitor += 60

    duration = time.time() - start_time
    send_rate = total_sent / duration if duration > 0 else 0
    recv_rate = total_received / duration if duration > 0 else 0
    loss_pct = (1 - (total_received / total_sent)) * 100 if total_sent > 0 else 0

    pub_client.loop_stop()
    sub_client.loop_stop()

    # --- Markdown speichern ---
    os.makedirs("latency_markdowns", exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_file = os.path.join("latency_markdowns", f"habapp_loadtest_qos{qos}_{timestamp_str}.md")

    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"# HABApp Lasttest QoS {qos}\n\n")
        f.write(f"- Dauer: {duration:.2f} s\n")
        f.write(f"- Gesendet: {total_sent}\n")
        f.write(f"- Empfangen: {total_received}\n")
        f.write(f"- Send-Rate: {send_rate:.2f} msg/s\n")
        f.write(f"- Empfangsrate: {recv_rate:.2f} msg/s\n")
        f.write(f"- Verlustquote: {loss_pct:.2f}%\n\n")

        if timeline:
            f.write("## Zwischenwerte\n\n")
            f.write("| Zeit (s) | Gesendet | Empfangen | Send-Rate (msg/s) | Empfangsrate (msg/s) | Verlust% |\n")
            f.write("|----------|----------|-----------|-------------------|----------------------|----------|\n")
            for t in timeline:
                f.write(f"| {t['Zeit_s']} | {t['Gesendet']} | {t['Empfangen']} | "
                        f"{t['Send-Rate']:.2f} | {t['Recv-Rate']:.2f} | {t['Verlust%']:.2f}% |\n")

        if cpu_series:
            f.write("\n## Systemmonitoring pro Minute\n\n")
            f.write("| Minute | CPU% | RAM% |\n")
            f.write("|--------|------|------|\n")
            for i, cpu in enumerate(cpu_series):
                f.write(f"| {timestamps[i]} | {cpu:.1f} | {ram_series[i]:.1f} |\n")

    print(f"\n📝 HABApp-Lasttest gespeichert unter: {md_file}")