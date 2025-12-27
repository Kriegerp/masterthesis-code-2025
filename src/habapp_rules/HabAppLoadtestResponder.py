import logging
import HABApp
from HABApp.mqtt.items import MqttItem
from HABApp.core.events import ValueUpdateEventFilter
import json
import time

log = logging.getLogger('MQTTEventBus')


class HabAppLoadtestResponder(HABApp.Rule):
    def __init__(self):
        super().__init__()

        self.cmd = MqttItem.get_create_item("/loadtest/habapp/input")
        self.cmd.listen_event(self.on_message, ValueUpdateEventFilter())

    def on_message(self, event):
        raw = event.value
        try:
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

            response = {
                "id": msg_id,
                "received_time": time.time(),
                "echo": data.get("echo", "ok")
            }

            self.mqtt.publish("/loadtest/habapp/response", json.dumps(response))
            log.info(f"Response gesendet für id={msg_id}")

        except Exception as e:
            log.error(f"Fehler im LoadtestResponder: {e}")


HabAppLoadtestResponder()