# utils.py
import os, statistics, json, glob
from datetime import datetime
from collections import defaultdict

def generate_payload(size_bytes: int, msg_id: str) -> str:
    content = "x" * max(0, size_bytes - 20)
    return json.dumps({"id": msg_id, "data": content})

def save_latency_csv(latency_data, mode: str, folder: str = "latency_logs_stability"):
    os.makedirs(folder, exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"latency_log_{mode}_{timestamp_str}.csv"
    filepath = os.path.join(folder, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("Timestamp;Latency_ms\n")
        for duration, latency in latency_data:
            f.write(f"{int(duration)};{latency:.2f}\n")
    print(f"✅ CSV gespeichert: {filepath}")
    return filepath

# def save_summary(latency_data, total_sent: int, total_received: int, filepath: str,
#                  mode: str, qos: int):
#     folder = os.path.dirname(filepath)
#     timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
#     duration_sec = latency_data[-1][0] if latency_data else 0
#     duration_min = duration_sec / 60 if duration_sec else 0
#     latencies = [l for _, l in latency_data]
#     avg = (sum(latencies) / len(latencies)) if latencies else 0
#     min_latency = min(latencies) if latencies else 0
#     max_latency = max(latencies) if latencies else 0
#     loss = ((total_sent - total_received) / total_sent * 100) if total_sent else 0

#     summary = [
#         f"Modus: {mode}",
#         f"Dauer: {duration_sec:.0f}s ({duration_min:.2f}min)",
#         f"Gesendet: {total_sent}",
#         f"Empfangen: {total_received}",
#         f"Durchschnitt: {avg:.2f}ms",
#         f"Minimum: {min_latency:.2f}ms",
#         f"Maximum: {max_latency:.2f}ms",
#         f"Verlustquote: {loss:.2f}%",
#         f"QoS: {qos}"
#     ]

#     summary_path = os.path.join(folder, f"summary_{mode}_{timestamp_str}.txt")
#     with open(summary_path, "w", encoding="utf-8") as f:
#         for line in summary:
#             f.write(line + "\n")
#     print("📋 Zusammenfassung gespeichert.")
#     return summary_path

import os, statistics, time

def save_summary(latency_data, total_sent, total_received, filepath, mode, qos, duration=None):
    """
    Speichert eine Zusammenfassung der Testergebnisse.
    - latency_data: Liste mit (timestamp, latency_ms) oder leer bei Durchsatztests
    - total_sent: Anzahl gesendeter Nachrichten
    - total_received: Anzahl empfangener Nachrichten
    - filepath: Dummy-Pfad oder Basisname (wird für Dateinamen genutzt)
    - mode: Testmodus (z. B. mqtt_echo, mqtt_throughput_combined)
    - qos: MQTT QoS-Level
    - duration: Dauer in Sekunden (optional, für Durchsatztests empfohlen)
    """

    # Ordner für Summaries
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_folder = "latency_summaries"
    os.makedirs(summary_folder, exist_ok=True)

    filename = os.path.join(summary_folder, f"summary_{mode}_{timestamp_str}.txt")

    with open(filename, "w") as f:
        f.write(f"Modus: {mode}\n")
        f.write(f"QoS: {qos}\n")

        # --- Durchsatztest ---
        if not latency_data:
            if duration is None:
                duration = 0
            duration_min = duration / 60 if duration else 0

            send_rate = total_sent / duration if duration > 0 else 0
            recv_rate = total_received / duration if duration > 0 else 0
            loss_pct = (1 - (total_received / total_sent)) * 100 if total_sent > 0 else 0

            f.write(f"Dauer: {duration:.2f}s ({duration_min:.2f}min)\n")
            f.write(f"Gesendet: {total_sent}\n")
            f.write(f"Empfangen: {total_received}\n")
            f.write(f"Send-Rate: {send_rate:.2f} msg/s\n")
            f.write(f"Recv-Rate: {recv_rate:.2f} msg/s\n")
            f.write(f"Verlustquote: {loss_pct:.2f}%\n")

        # --- Latenztest ---
        else:
            latencies = [lat for _, lat in latency_data]
            avg = statistics.mean(latencies) if latencies else 0
            min_lat = min(latencies) if latencies else 0
            max_lat = max(latencies) if latencies else 0

            duration = duration or (latency_data[-1][0] if latency_data else 0)
            duration_min = duration / 60 if duration else 0

            f.write(f"Dauer: {duration:.2f}s ({duration_min:.2f}min)\n")
            f.write(f"Gesendet: {total_sent}\n")
            f.write(f"Empfangen: {total_received}\n")
            f.write(f"Durchschnitt: {avg:.2f} ms\n")
            f.write(f"Minimum: {min_lat:.2f} ms\n")
            f.write(f"Maximum: {max_lat:.2f} ms\n")

    print("📋 Zusammenfassung gespeichert:", filename)
    return filename

# def save_markdown_table(summaries, output_folder: str = "latency_markdowns"):
#     os.makedirs(output_folder, exist_ok=True)
#     timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"latency_summary_{timestamp_str}.md"
#     output_path = os.path.join(output_folder, filename)

#     with open(output_path, "w", encoding="utf-8") as f:
#         f.write("| Modus | Gesendet | Empfangen | Verlust% | Ø Latenz (ms) | Min (ms) | Max (ms) |\n")
#         f.write("|-------|----------|-----------|----------|---------------|----------|----------|\n")
#         for s in summaries:
#             f.write(f"| {s['Modus']} | {s['Gesendet']} | {s['Empfangen']} | {s['Verlust']:.2f} | {s['Ø Latenz']:.2f} | {s['Min']:.2f} | {s['Max']:.2f} |\n")
#     print(f"📝 Markdown-Tabelle gespeichert unter: {output_path}")
#     return output_path

def save_markdown_table(summaries, output_folder: str = "latency_markdowns"):
    import os
    from datetime import datetime

    os.makedirs(output_folder, exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"latency_summary_{timestamp_str}.md"
    output_path = os.path.join(output_folder, filename)

    # Reihenfolge festlegen
    order = ["mqtt_echo", "habapp_echo", "openhab_bridge_echo"]
    summaries_sorted = sorted(summaries, key=lambda s: order.index(s["Modus"]) if s["Modus"] in order else 99)

    # Header mit Datum
    header = f"# Zusammenfassung der Echo-Modi\n\n**Datum:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    # Tabellenkopf
    table_header = (
        "| Modus | Dauer | Gesendet | Empfangen | Ø Latenz (ms) | Verlust (%) | QoS | Min (ms) | Max (ms) |\n"
        "|-------|-------|----------|-----------|---------------|-------------|-----|----------|----------|\n"
    )

    # Tabellenzeilen
    rows = []
    for s in summaries_sorted:
        rows.append(
            f"| {s['Modus']} | {s['Dauer_str']} | {s['Gesendet']} | {s['Empfangen']} | "
            f"{s['Ø Latenz']:.2f} | {s['Verlust']:.2f} | {s['QoS']} | {s['Min']:.2f} | {s['Max']:.2f} |"
        )

    # Segmentanalyse berechnen
    lat_map = {s["Modus"]: s["Ø Latenz"] for s in summaries_sorted}
    segment_md = ""
    if all(k in lat_map for k in ["mqtt_echo", "habapp_echo", "openhab_bridge_echo"]):
        mqtt_to_habapp = lat_map["habapp_echo"] - lat_map["mqtt_echo"]
        habapp_to_openhab = lat_map["openhab_bridge_echo"] - lat_map["habapp_echo"]

        segment_md = (
            "\n\n## Segmentanalyse der Latenzpfade\n\n"
            "| Segment | Ø Latenz (ms) |\n"
            "|---------|---------------|\n"
            f"| MQTT → HABApp | {mqtt_to_habapp:.2f} |\n"
            f"| HABApp → openHAB | {habapp_to_openhab:.2f} |\n"
        )

    # Datei schreiben
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write(table_header)
        f.write("\n".join(rows))
        if segment_md:
            f.write(segment_md)

    print(f"📝 Markdown-Tabelle gespeichert unter: {output_path}")
    return output_path

# def summarize_all_results(folder: str = "latency_summaries"):
#     summaries = []
#     files_by_mode = defaultdict(list)

#     for file in glob.glob(os.path.join(folder, "summary_*.txt")):
#         try:
#             with open(file, "r", encoding="utf-8") as f:
#                 first_line = f.readline().strip()
#                 if first_line.startswith("Modus: "):
#                     mode = first_line.split(": ")[1]
#                     files_by_mode[mode].append(file)
#         except Exception as e:
#             print(f"⚠️ Fehler beim Lesen von Datei: {file} → {e}")

#     latest_files = [sorted(files)[-1] for files in files_by_mode.values()]

#     for file in latest_files:
#         try:
#             with open(file, "r", encoding="utf-8") as f:
#                 lines = [line.strip() for line in f.readlines()]
#                 loss_raw = lines[5].split(": ")[1]  # je nach Position anpassen
#                 loss_clean = loss_raw.replace("%", "").replace("ms", "").strip()

#                 raw_duration = lines[2].split(": ")[1]  # "59.08s (0.98min)"
#                 duration_sec = float(raw_duration.split("s")[0])

#                 summary = {
#                     "Modus": lines[0].split(": ")[1],
#                     "QoS": lines[1].split(": ")[1],
#                     "Dauer": duration_sec,
#                     "Dauer_str": raw_duration,
#                     "Gesendet": int(lines[3].split(": ")[1]),
#                     "Empfangen": int(lines[4].split(": ")[1]),
#                     "Ø Latenz": float(lines[5].split(": ")[1].replace("ms", "").strip()),
#                     "Verlust": float(loss_clean),
#                 }


#                 csv_file = file.replace("summary_", "latency_log_").replace(".txt", ".csv")
#                 try:
#                     with open(csv_file, "r", encoding="utf-8") as cf:
#                         latencies = [float(line.split(";")[1]) for line in cf.readlines()[1:]]
#                         summary["Min"] = min(latencies) if latencies else 0.0
#                         summary["Max"] = max(latencies) if latencies else 0.0
#                 except Exception as e:
#                     print(f"⚠️ CSV konnte nicht gelesen werden: {csv_file} → {e}")
#                     summary["Min"] = 0.0
#                     summary["Max"] = 0.0
#                 summaries.append(summary)

#         except Exception as e:
#             print(f"⚠️ Fehler beim Verarbeiten von Datei: {file} → {e}")
#             continue

#     return summaries

def summarize_all_results(folder: str = "latency_summaries"):
    import glob, os
    summaries = []
    files_by_mode = {}

    # Nur Echo-Modi berücksichtigen
    valid_modes = {"mqtt_echo", "habapp_echo", "openhab_bridge_echo"}

    # Alle Summary-Dateien einsammeln
    for file in glob.glob(os.path.join(folder, "summary_*.txt")):
        try:
            with open(file, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if first_line.startswith("Modus: "):
                    mode = first_line.split(": ")[1]
                    if mode in valid_modes:
                        files_by_mode.setdefault(mode, []).append(file)
        except Exception as e:
            print(f"⚠️ Fehler beim Lesen von Datei: {file} → {e}")

    # Neueste Datei pro Modus
    latest_files = [sorted(files)[-1] for files in files_by_mode.values()]

    for file in latest_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines()]

                raw_duration = lines[2].split(": ")[1]  # "59.08s (0.98min)"
                duration_sec = float(raw_duration.split("s")[0])

                summary = {
                    "Modus": lines[0].split(": ")[1],
                    "QoS": lines[1].split(": ")[1],
                    "Dauer": duration_sec,
                    "Dauer_str": raw_duration,
                    "Gesendet": int(lines[3].split(": ")[1]),
                    "Empfangen": int(lines[4].split(": ")[1]),
                    "Ø Latenz": float(lines[5].split(": ")[1].replace("ms", "").strip()),
                    "Min": float(lines[6].split(": ")[1].replace("ms", "").strip()),
                    "Max": float(lines[7].split(": ")[1].replace("ms", "").strip()),
                    "Verlust": float(lines[8].split(": ")[1].replace("%", "").strip()) if len(lines) > 8 else 0.0,
                }

                # CSV optional lesen
                csv_file = file.replace("summary_", "latency_log_").replace(".txt", ".csv")
                if os.path.exists(csv_file):
                    try:
                        with open(csv_file, "r", encoding="utf-8") as cf:
                            latencies = [float(line.split(";")[1].replace(",", ".")) for line in cf.readlines()[1:]]
                            summary["Min"] = min(latencies) if latencies else summary["Min"]
                            summary["Max"] = max(latencies) if latencies else summary["Max"]
                    except Exception as e:
                        print(f"⚠️ CSV konnte nicht gelesen werden: {csv_file} → {e}")
                else:
                    # Kein CSV vorhanden → Min/Max bleiben wie im Summary-File
                    pass

                summaries.append(summary)

        except Exception as e:
            print(f"⚠️ Fehler beim Verarbeiten von Datei: {file} → {e}")
            continue

    return summaries

def compute_component_latencies(summaries):
    lat_map = {s["Modus"]: s["Ø Latenz"] for s in summaries}
    if not all(k in lat_map for k in ["mqtt_echo", "habapp_echo", "openhab_bridge_echo"]):
        print("⚠️ Segmentanalyse nicht möglich – unvollständige Modi.")
        return None

    mqtt_to_habapp = lat_map["habapp_echo"] - lat_map["mqtt_echo"]
    habapp_to_openhab = lat_map["openhab_bridge_echo"] - lat_map["habapp_echo"]

    print("\n🔍 Segmentanalyse (Differenz der Ø-Latenzen):")
    print(f"MQTT → HABApp:         {mqtt_to_habapp:.2f} ms")
    print(f"HABApp → openHAB:      {habapp_to_openhab:.2f} ms")
    return {"mqtt_to_habapp": mqtt_to_habapp, "habapp_to_openhab": habapp_to_openhab}

def save_segment_markdown(summaries, output_folder: str = "latency_markdowns"):
    os.makedirs(output_folder, exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"latency_segments_{timestamp_str}.md"
    output_path = os.path.join(output_folder, filename)

    lat_map = {s["Modus"]: s["Ø Latenz"] for s in summaries}
    if not all(k in lat_map for k in ["mqtt_echo", "habapp_echo", "openhab_bridge_echo"]):
        print("⚠️ Segmentanalyse nicht möglich – unvollständige Modi.")
        return None

    mqtt_to_habapp = lat_map["habapp_echo"] - lat_map["mqtt_echo"]
    habapp_to_openhab = lat_map["openhab_bridge_echo"] - lat_map["habapp_echo"]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Segmentanalyse der Latenzpfade\n\n")
        f.write("| Segment | Ø Latenz (ms) |\n")
        f.write("|---------|----------------|\n")
        f.write(f"| MQTT → HABApp | {mqtt_to_habapp:.2f} |\n")
        f.write(f"| HABApp → openHAB | {habapp_to_openhab:.2f} |\n")

    print(f"📝 Segmentanalyse gespeichert unter: {output_path}")
    return output_path