"""
Worker class to download album art images.
"""

import logging as log
import os
import threading
import urllib

import eyed3

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot

from . import BASE_PATH
from . import music_library as mdb


class LibraryImageBuilder(QThread):
    def __init__(self, music_library, artists):
        super().__init__()
        self.music_library = music_library
        self.artists = artists
        self.icon_data = {}
        try:
            self._empty_image = open(os.path.join(BASE_PATH, "icons", "no_artwork.png"), "rb").read()
        except Exception:
            self._empty_image = b""

    def run(self):
        threading.current_thread().name = "AlbumArtThread"
        self.stop_thread=False

        mdb.connect_db()
        music_library = self.music_library
        artists = self.artists

        # collect icons
        for i, artist in enumerate(artists):
            if self.stop_thread:
                return
            last_date = -1
            albums = music_library.get_albums_for_artist(artist.title)
            for album in albums:
                img_data, date = mdb.get_image(artist.title, album.title)
                if img_data is None:
                    try:
                        rtrack = music_library.get_tracks_for_album(
                            artist.title, album.title, full_album_art_uri=True
                        ).pop()
                        uri = rtrack.album_art_uri
                        rtfile = rtrack.get_uri()
                        if rtfile.startswith("x-file-cifs:"):
                            rtpath = urllib.request.unquote(rtfile.split(":", 1)[1])
                            rmp3 = eyed3.load(rtpath)
                        else:
                            date = 0
                            img_data = self._empty_image
                    except Exception:
                        log.warning(f"Error getting track info for {rtpath}")
                    else:
                        try:
                            date = int(str(rmp3.tag.getBestDate()))
                        except (ValueError, AttributeError):
                            log.warning(f"Tag error for {rtpath}")
                            date = 0
                        try:
                            img_data = urllib.request.urlopen(uri).read()
                        except Exception:
                            log.warning(f"Could not fetch artwork for {artist.title} | {album.title}", exc_info=True)
                            img_data = self._empty_image
                    mdb.insert_image(artist.title, album.title, img_data, date)
                if date > last_date:
                    self.icon_data[artist.title] = img_data
                    last_date = date
            self.download_progress.emit((i + 1) / len(artists))

    download_progress = pyqtSignal(float)

    def quit(self):
        self.stop_thread=True
        return super().quit()
