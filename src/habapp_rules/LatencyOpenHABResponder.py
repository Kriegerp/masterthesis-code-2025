import HABApp
import json
import time
import asyncio
from HABApp.mqtt.items import MqttItem, MqttPairItem
from HABApp.openhab.items import OpenhabItem
from HABApp.core import Items
from HABApp.core.errors import ItemNotFoundException
from HABApp.core.events import ValueChangeEvent
import logging


log = logging.getLogger('MQTTEventBus')
#log_state = True  # Parameter('mqtt_event_bus', 'log_state', default_value=False).value

class LatencyOpenHABResponder(HABApp.Rule):
    def __init__(self):
        super().__init__()

        self.command_queue = asyncio.Queue()
        self.command_times = {}  # msg_id → timestamp
        self.mqtt_pairs = {}
        self.payload = None

        # Nur gezielte Items verwenden
        self.item_name = "testSwitch"
        self.cmd_topic = "/latency/openhab/command"
        self.state_topic = "/latency/openhab/state"

        try:
            existing = Items.get_item(self.cmd_topic)
            if not isinstance(existing, MqttPairItem):
                Items.pop_item(self.cmd_topic)
        except ItemNotFoundException:
            pass

        # MQTT-Item für Command abonnieren
        mqtt_pair = MqttPairItem.get_create_item(
            self.cmd_topic, write_topic=self.state_topic)
        self.mqtt_pairs[self.item_name] = mqtt_pair

        # Command Event Listener registrieren
        mqtt_pair.listen_event(self.on_mqtt_command)

        # openHAB-Item abonnieren
        self.item = OpenhabItem.get_item(self.item_name)
        self.item.listen_event(self.on_item_state)

        # Hintergrundprozess starten
        self.run.soon(self.process_queue)

    async def process_queue(self):
        while True:
            item_name, value = await self.command_queue.get()
            self.command_times[item_name] = time.time()
            self.openhab.send_command(item_name, value)

    async def on_mqtt_command(self, event: ValueChangeEvent):
        try:
            # if self.item_name in event.name:
            self.payload = event.value
            value = self.payload.get("command")
            if value is not None:
                self.command_queue.put_nowait((self.item_name, value))
        except Exception as e:
            log.error(f"Fehler beim Parsen des Commands: {e}")

    def on_item_state(self, event: ValueChangeEvent):
        if self.item_name in event.name:
        #    mqtt_item = self.mqtt_pair
            mqtt_item = self.mqtt_pairs.get(event.name)
            if not mqtt_item:
                return

            # robust gegen ItemStateUpdatedEvent und ValueChangeEvent
            old_value = getattr(event, "old_value", None)
            if old_value != event.value:

            #mqtt_item = self.mqtt_pairs.get(event.name)
            #if mqtt_item and event.old_value != event.value:
                if event.name in self.command_times:
                    response = {
                        "id": self.payload.get("id"),
                        "item": self.item_name,
                        "client_timestamp": self.payload.get("client_timestamp"),
                        "command": self.payload.get("command"),
                        "state": str(event.value),
                        "openhab_command_time": self.command_times.pop(event.name),
                        "openhab_state_time": time.time()
                    }
                    mqtt_item.publish(json.dumps(response), qos=0)


LatencyOpenHABResponder()
