"""
Simple working thread to prevent connecting to Sonos system from blocking the GUI at startup.
"""

import logging as log
import threading

from time import sleep

import soco

from PyQt5.QtCore import QObject, QTimer, pyqtSlot

from .data_model import SonosSpeaker, SonosSystem


class SonosConnector(QObject):
    system: SonosSystem = None

    @pyqtSlot()
    def setup_sonos(self):
        threading.current_thread().name = "SonosConnectorThread"

        speakers = []
        try:
            for item in soco.discover():
                si = item.get_speaker_info()
                speaker = SonosSpeaker(item.ip_address, si["model_name"], si["zone_name"], item)
                speakers.append(speaker)
        except Exception:
            log.warning("Could not connect to Sonos, try again in 5 s.", exc_info=True)
            QTimer.singleShot(5000, self.setup_sonos)
        else:
            self.system = SonosSystem(speakers)
