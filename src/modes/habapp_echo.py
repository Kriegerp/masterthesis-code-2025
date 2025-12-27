# modes/habapp_echo.py
import time, json, paho.mqtt.client as mqtt
from utils import save_latency_csv, save_summary
from plot_latency import plot_latency

def run_habapp_echo(args, BROKER_IP):
    latency_data = []
    sent_timestamps = {}
    total_sent = total_received = 0

    def on_message(client, userdata, msg):
        nonlocal total_received
        try:
            payload = json.loads(msg.payload.decode())
            msg_id = payload.get("id")
            if msg_id and msg_id in sent_timestamps:
                latency = (time.time() - sent_timestamps.pop(msg_id)) * 1000
                duration = time.time() - start_time
                latency_data.append((duration, latency))
                print(f"📨 [Echo] {msg_id}: {latency:.2f} ms")
                total_received += 1
            else:
                print(f"⚠️ [Echo] Ignoriert: Keine passende ID für {msg.payload.decode()}")
        except Exception as e:
            print("Fehler beim Verarbeiten der Antwort:", e)

    client = mqtt.Client()
    client.on_message = on_message
    client.connect(BROKER_IP, 1883)
    client.subscribe("/latency/habapp/echo/response", qos=0)
    client.loop_start()

    start_time = time.time()
    i = 0

    while True:
        now = time.time()
        if now - start_time >= args.duration * 60:
            break
        i += 1
        msg_id = f"msg_{i}"
        payload = json.dumps({"id": msg_id, "data": now})
        print(f"➡️ [Echo] Gesendet: {payload}")
        client.publish("/latency/habapp/echo", payload, qos=args.qos)
        sent_timestamps[msg_id] = now
        total_sent += 1
        time.sleep(args.delay)

    time.sleep(5)
    client.loop_stop()
    path = save_latency_csv(latency_data, args.mode)
    save_summary(latency_data, total_sent, total_received, filepath="habapp_echo", mode="habapp_echo", qos=args.qos)
    plot_latency(path, output_folder="latency_plots")