import asyncio
import logging
from HABApp.openhab.items import OpenhabItem
from HABApp.mqtt.items import MqttPairItem
from HABApp.core.events import ValueChangeEvent
from HABApp.core import Items
from HABApp.core.errors import ItemNotFoundException
from HABApp import Parameter
import HABApp

log = logging.getLogger('MQTTEventBus')
# Parameter('mqtt_event_bus', 'log_state', default_value=False).value
log_state = True


class MqttOpenHABBridge(HABApp.Rule):
    def __init__(self):
        super().__init__()

        self.mqtt_pairs = {}   # OpenHAB-Item-Name -> MqttPairItem
        self.topic_map = {}    # MQTT Command-Topic -> OpenHAB-Item-Name

        # Async Queue für eingehende Commands
        self.command_queue = asyncio.Queue()

        # Alle OpenHAB-Items holen und MqttPairItem erstellen
        for item in self.get_items(type=OpenhabItem):
            cmd_topic = f"/messages/commands/{item.name}"
            state_topic = f"/messages/states/{item.name}"

            # Prüfen, ob Item bereits existiert
            try:
                existing = Items.get_item(cmd_topic)
                if not isinstance(existing, MqttPairItem):
                    log.warning(
                        f"Item {cmd_topic} existiert bereits als {type(existing).__name__}, ersetze durch MqttPairItem"
                    )
                    Items.pop_item(cmd_topic)
            except ItemNotFoundException:
                pass

            # MqttPairItem erzeugen
            mqtt_pair = MqttPairItem.get_create_item(
                cmd_topic, write_topic=state_topic)
            self.mqtt_pairs[item.name] = mqtt_pair
            self.topic_map[cmd_topic] = item.name

            # Event-Listener registrieren
            mqtt_pair.listen_event(self.on_mqtt_command)
            item.listen_event(self.on_item_state)

        # Background-Task für Queue starten
        # asyncio.create_task(self.process_queue())
        # self.run_coro(self.process_queue())
        self.run.soon(self.process_queue)

    async def process_queue(self):
        """Verarbeitet Commands aus der Queue und sendet sie an OpenHAB"""
        while True:
            item_name, value = await self.command_queue.get()
            try:
                self.openhab.send_command(item_name, value)
                if log_state:
                    log.info(
                        f"MQTT Command {value} -> OpenHAB Item {item_name}")
            except Exception as e:
                log.warning(
                    f"Fehler beim Senden an OpenHAB Item {item_name}: {e}")

    async def on_mqtt_command(self, event: ValueChangeEvent):
        """MQTT-Command kommt rein -> in Queue einreihen"""
        item_name = self.topic_map.get(event.name)
        if not item_name:
            log.warning(f"No OpenHAB mapping for {event.name}")
            return

        # Command async in Queue einreihen
        self.command_queue.put_nowait((item_name, event.value))

    def on_item_state(self, event: ValueChangeEvent):
        """OpenHAB-Item-Update -> MQTT publishen"""
        mqtt_item = self.mqtt_pairs.get(event.name)
        if mqtt_item and event.old_value != event.value:
            mqtt_item.publish(str(event.value))
            if log_state:
                log.info(
                    f"OpenHAB {event.name} -> MQTT {mqtt_item.write_topic} = {event.value}")


# Regel initialisieren
MqttOpenHABBridge()
