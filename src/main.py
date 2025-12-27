# main.py
import argparse
from modes.mqtt_echo import run_mqtt_echo
from modes.mqtt_pub import run_mqtt_pub
from modes.habapp_echo import run_habapp_echo
from modes.openhab_bridge_echo import run_openhab_bridge_echo
from modes.compare_echo_modes import run_compare_echo_modes
from modes.mqtt_throughput import run_mqtt_throughput
from modes.mqtt_throughput_combined import run_mqtt_throughput_combined
from modes.mqtt_stresstest import run_mqtt_stresstest
from modes.mqtt_stresstest_combined import run_mqtt_stresstest_combined
from modes.mqtt_loadtest import run_mqtt_loadtest
from modes.mqtt_loadtest_combined import run_mqtt_loadtest_combined
from modes.habapp_throughput import run_habapp_throughput
from modes.habapp_stresstest import run_habapp_stresstest
from modes.habapp_stresstest_combined import run_habapp_stresstest_combined
from modes.habapp_loadtest import run_habapp_loadtest
from modes.habapp_loadtest_combined import run_habapp_loadtest_combined
from modes.habapp_throughput_combined import run_habapp_throughput_combined
from modes.openhab_throughput import run_openhab_throughput
from modes.openhab_throughput_combined import run_openhab_throughput_combined
from modes.openhab_loadtest_combined import run_openhab_loadtest_combined
from modes.openhab_stresstest import run_openhab_stresstest
from modes.openhab_stresstest_combined import run_openhab_stresstest_combined
from modes.openhab_loadtest import run_openhab_loadtest

BROKER_IP = "192.168.0.5"

parser = argparse.ArgumentParser(description="Smart Home Test Runner")
parser.add_argument("--mode", type=str, required=True)
parser.add_argument("--duration", type=int, default=10)
parser.add_argument("--delay", type=float, default=1.0)
parser.add_argument("--qos", type=int, default=1)
parser.add_argument("--payload_size", type=int, default=64)
parser.add_argument("--item", type=str)
parser.add_argument("--topic", type=str, default="latency/test")
parser.add_argument("--pause_between_qos", type=int, default=5)
args = parser.parse_args()

dispatch = {
    "mqtt_echo": run_mqtt_echo,
    "mqtt_pub": run_mqtt_pub,
    "habapp_echo": run_habapp_echo,
    "openhab_bridge_echo": run_openhab_bridge_echo,
    "compare_echo_modes": run_compare_echo_modes,
    "mqtt_throughput": run_mqtt_throughput,
    "mqtt_throughput_combined": run_mqtt_throughput_combined,
    "mqtt_stresstest": run_mqtt_stresstest,
    "mqtt_stresstest_combined": run_mqtt_stresstest_combined,
    "mqtt_loadtest": run_mqtt_loadtest,
    "mqtt_loadtest_combined": run_mqtt_loadtest_combined,
    "habapp_throughput": run_habapp_throughput,
    "habapp_stresstest": run_habapp_stresstest,
    "habapp_stresstest_combined": run_habapp_stresstest_combined,
    "habapp_loadtest": run_habapp_loadtest,
    "habapp_loadtest_combined": run_habapp_loadtest_combined,
    "habapp_throughput_combined": run_habapp_throughput_combined,
    "openhab_throughput": run_openhab_throughput,
    "openhab_throughput_combined": run_openhab_throughput_combined,
    "openhab_loadtest_combined": run_openhab_loadtest_combined,
    "openhab_stresstest": run_openhab_stresstest,
    "openhab_stresstest_combined": run_openhab_stresstest_combined,
    "openhab_loadtest": run_openhab_loadtest,
}

fn = dispatch.get(args.mode)
if fn:
    fn(args, BROKER_IP)
else:
    print("❌ Unbekannter Modus:", args.mode)