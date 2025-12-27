import logging
import HABApp
from HABApp.mqtt.items import MqttItem
from HABApp.core.events import ValueUpdateEventFilter
import json
import time

log = logging.getLogger('MQTTEventBus')


class HabAppThroughputResponder(HABApp.Rule):
    def __init__(self):
        super().__init__()

        # Eingangs-Topic für Durchsatztest
        self.cmd = MqttItem.get_create_item("/throughput/habapp/input")

        # Wie im Loadtest: nur auf ValueUpdateEvent reagieren (kein Change/Restore etc.)
        self.cmd.listen_event(self.on_message, ValueUpdateEventFilter())

    def on_message(self, event):
        raw = event.value
        try:
            # JSON sicherstellen
            if isinstance(raw, str):
                data = json.loads(raw)
            elif isinstance(raw, dict):
                data = raw
            else:
                log.warning(f"Unerwarteter Datentyp: {type(raw)}")
                return

            msg_id = data.get("id")
            if msg_id is None:
                log.warning("kein 'id'-Feld im Payload gefunden.")
                return

            # Antwortobjekt bauen
            response = {
                "id": msg_id,
                "received_time": time.time(),
                "echo": data.get("echo", "ok")
            }

            # Antwort publizieren
            self.mqtt.publish("/throughput/habapp/response", json.dumps(response))
            log.info(f"Response gesendet für id={msg_id}")

        except Exception as e:
            log.error(f"Fehler im ThroughputResponder: {e}")


HabAppThroughputResponder()