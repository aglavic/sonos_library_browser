"""
Simple working thread to prevent connecting to Sonos system from blocking the GUI at startup.
"""

import logging as log
import threading

from time import sleep

import soco

from PyQt5.QtCore import QMutex, QThread

from .data_model import SonosSpeaker, SonosSystem


class SonosConnector(QThread):
    system: SonosSystem = None

    def run(self):
        threading.current_thread().name = "SonosConnectorThread"
        self.stop_thread = False
        self.mutex = QMutex()

        while not self.stop_thread and self.system is None:
            self.setup_sonos()

    def setup_sonos(self):
        speakers = []
        try:
            for item in soco.discover():
                si = item.get_speaker_info()
                speaker = SonosSpeaker(item.ip_address, si["model_name"], si["zone_name"], item)
                speakers.append(speaker)
        except Exception:
            log.warning("Could not connect to Sonos, try again in 5 s.", exc_info=True)
            self.mutex.lock()
            self.mutex.tryLock(5000)
            self.mutex.unlock()
        else:
            self.system = SonosSystem(speakers)

    def quit(self):
        self.stop_thread = True
        self.mutex.unlock()
        return super().quit()
