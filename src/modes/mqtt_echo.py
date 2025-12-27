# modes/mqtt_echo.py
import time, json, paho.mqtt.client as mqtt
from utils import save_latency_csv, save_summary
from plot_latency import plot_latency

def run_mqtt_echo(args, BROKER_IP):
    latency_data, sent_timestamps = [], {}
    total_sent = total_received = 0

    def on_message(client, userdata, msg):
        nonlocal total_received
        payload = json.loads(msg.payload.decode())
        msg_id = payload.get("id")
        if msg_id and msg_id in sent_timestamps:
            t_sent = sent_timestamps.pop(msg_id)
            latency_ms = (time.time() - t_sent) * 1000
            duration = time.time() - start_time
            latency_data.append((duration, latency_ms))
            print(f"📨 {msg_id}: {latency_ms:.2f} ms")
            total_received += 1

    client = mqtt.Client()
    client.on_message = on_message
    client.connect(BROKER_IP, 1883)
    client.subscribe(args.topic, qos=args.qos)
    client.loop_start()

    start_time = time.time()
    i = 0
    while time.time() - start_time < args.duration * 60:
        i += 1
        msg_id = f"msg_{i}"
        now = time.time()
        payload = json.dumps({"id": msg_id, "data": now})
        client.publish(args.topic, payload, qos=args.qos)
        sent_timestamps[msg_id] = now
        total_sent += 1
        time.sleep(args.delay)

    time.sleep(5)
    client.loop_stop()
    path = save_latency_csv(latency_data, mode=args.mode)
    save_summary(latency_data, total_sent, total_received, filepath="mqtt_echo", mode="mqtt_echo", qos=args.qos)
    plot_latency(path, output_folder="latency_plots")