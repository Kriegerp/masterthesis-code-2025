import matplotlib.pyplot as plt
import csv
import os
import datetime

def plot_latency(csv_path, output_folder="latency_plots"):
    timestamps = []
    latencies = []

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)  # Header überspringen
        for row in reader:
            try:
                time_s = int(row[0])
                latency_ms = float(row[1].replace(",", "."))
                timestamps.append(time_s)
                latencies.append(latency_ms)
            except:
                continue 

    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, latencies, marker="o", linestyle="-", color="blue", label="Latenz (ms)")
    plt.title("MQTT Latenz über Zeit")
    plt.xlabel("Zeit (s)")
    plt.ylabel("Latenz (ms)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    # Ordner erstellen
    os.makedirs(output_folder, exist_ok=True)

    # Dateiname mit Zeitstempel
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"latenz_plot_{timestamp}.png"
    filepath = os.path.join(output_folder, filename)

    # Diagramm speichern
    plt.savefig(filepath)
    print(f"Diagramm gespeichert unter {filepath}")

# Beispielaufruf
# plot_latency("latency_logs_stability/latency_log_20250821_145851.csv")