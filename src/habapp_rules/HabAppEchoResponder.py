import logging
import HABApp
from HABApp.mqtt.items import MqttItem
from HABApp.core.events import ValueChangeEvent
import json
import time

log = logging.getLogger('MQTTEventBus')


class HabAppEchoResponder(HABApp.Rule):
    def __init__(self):
        super().__init__()
        self.last_ts = 0.0  # letzter verarbeiteter Zeitstempel

        # Topic abonnieren
        self.cmd = MqttItem.get_create_item("/latency/habapp/echo")
        self.cmd.listen_event(self.on_command)

    def on_command(self, event: ValueChangeEvent):
        raw = event.value
        log.warning(f"Eingehender Payload: {raw} ({type(raw)})")

        try:
            # sicherstellen, dass wir ein dict haben
            if isinstance(raw, str):
                data = json.loads(raw)
            elif isinstance(raw, dict):
                data = raw
            else:
                log.warning(f"Unerwarteter Datentyp: {type(raw)}")
                return

            # Zeitstempel holen
            ts = float(data.get("data", 0))
            if ts <= self.last_ts:
                log.info(f"Älterer Timestamp{ts}, wird ignoriert.")
                return

            # Aktueller Zeitstempel wird gespeichert
            self.last_ts = ts

            # benötigter Felder holen
            msg_id = data.get("id")
            echo = data.get("echo")

            if msg_id is None:
               log.warning("kein 'id'-Feld im Payload gefunden.")
               return

            # Antwortobjekt bauen
            response = {
                "id": msg_id,
                "echo": echo or "pong", #falls echo fehlt -> Standard
                "original": ts,
                "habapp_time": time.time(),
            }

            # Antwort publizieren
            self.mqtt.publish("/latency/habapp/echo/response",
                              json.dumps(response))
            log.info(f"Echo gesendet für {msg_id}")

        except (json.JSONDecodeError, TypeError) as e:
            log.error(f"Ungültiges JSON empfangen: {e}")
        except Exception as e:
            log.error(f"Fehler beim Echo: {e}")
        return


HabAppEchoResponder()
