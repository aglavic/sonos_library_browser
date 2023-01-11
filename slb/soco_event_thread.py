"""
A QThread class that listens to soco events and triggers a signal if one is present.
"""

import logging as log

import soco

from PyQt5.QtCore import QThread, pyqtSignal
from soco.events import event_listener


class SocoEventThread(QThread):
    zone_topology_event = pyqtSignal()

    def __init__(self, controller: soco.SoCo):
        super().__init__()
        self.stop_thread = False

        self.subscription = controller.zoneGroupTopology.subscribe()
        try:
            # there is always a first event when subscribing
            self.subscription.events.get(timeout=0.5)
        except Exception:
            pass

    def run(self):
        while not self.stop_thread:
            try:
                event = self.subscription.events.get(timeout=0.5)
            except Exception:
                pass
            else:
                if "zone_group_state" in event.variables:
                    log.info("Received Sonos Zone event")
                    self.zone_topology_event.emit()
        self.subscription.unsubscribe()
        event_listener.stop()

    def quit(self):
        self.stop_thread = True
        super().quit()
