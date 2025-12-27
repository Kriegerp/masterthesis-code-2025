# modes/openhab_bridge_echo.py
import time, json, paho.mqtt.client as mqtt
from utils import save_latency_csv, save_summary
from plot_latency import plot_latency

def run_openhab_bridge_echo(args, BROKER_IP):
    command = "ON"
    latency_data = []
    sent_timestamps = {}
    total_sent = total_received = 0

    def on_message(client, userdata, msg):
        nonlocal command, total_received
        try:
            payload = json.loads(msg.payload.decode())
            msg_id = payload.get("id")
            cmd_ts = payload.get("openhab_command_time")
            state_ts = payload.get("openhab_state_time")
            # command = "ON" if payload.get("state") == "OFF" else "OFF"
            value = payload.get("value")

            if value in ("ON", "OFF"):
              command = "ON" if value == "OFF" else "OFF"

            # Latenzberechnung
            if msg_id and isinstance(cmd_ts, (int, float)) and isinstance(state_ts, (int, float)):
                latency = (state_ts - cmd_ts) * 1000
                duration = time.time() - start_time
                latency_data.append((duration, latency))
                print(f"📨 [openHAB Bridge] {msg_id}: {latency:.2f} ms")
                total_received += 1
            else:
                print(f"⚠️ Ungültige Zeitstempel oder msg_id in Antwort: {payload}")

        except Exception as e:
            print("Fehler beim Verarbeiten der Antwort:", e)

    client = mqtt.Client()
    client.on_message = on_message
    client.connect(BROKER_IP, 1883)
    client.subscribe("/latency/openhab/state", qos=0)
    client.loop_start()

    start_time = time.time()
    i = 0

    while True:
        now = time.time()
        if now - start_time >= args.duration * 60:
            break
        i += 1
        msg_id = f"msg_{i}"
        payload = json.dumps({"id": msg_id, "client_timestamp": now, "command": command})
        print(f"➡️ [openHAB Bridge] Gesendet: {payload}")
        client.publish("/latency/openhab/command", payload, qos=args.qos)
        sent_timestamps[msg_id] = now
        total_sent += 1
        time.sleep(args.delay)

    time.sleep(5)
    client.loop_stop()
    path = save_latency_csv(latency_data, args.mode)
    save_summary(latency_data, total_sent, total_received, filepath="openhab_bridge_echo", mode="openhab_bridge_echo", qos=args.qos)
    plot_latency(path, output_folder="latency_plots")