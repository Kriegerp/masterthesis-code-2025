from modes.mqtt_echo import run_mqtt_echo
from modes.habapp_echo import run_habapp_echo
from modes.openhab_bridge_echo import run_openhab_bridge_echo
from utils import summarize_all_results
from utils import save_markdown_table

def run_compare_echo_modes(args, BROKER_IP):
    MODI = [
        ("mqtt_echo", run_mqtt_echo),
        ("habapp_echo", run_habapp_echo),
        ("openhab_bridge_echo", run_openhab_bridge_echo),
    ]

    for mode_name, fn in MODI:
        print(f"\n🚀 Starte Modus: {mode_name}")
        fn(args, BROKER_IP)

    print("\n📊 Alle Echo-Modi abgeschlossen. Starte Zusammenfassung…")
    summaries = summarize_all_results()
    save_markdown_table(summaries)