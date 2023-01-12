"""
The central main window class for the GUI.
"""
import logging
import logging as log
import os
import urllib

from PyQt5 import QtCore, QtGui, QtWidgets

from . import BASE_PATH, main_interface
from . import music_library as mdb
from .custom_logging import QtLogger
from .data_model import SonosGroup, SonosSpeaker, SonosSystem
from .image_builder import LibraryImageBuilder
from .soco_event_thread import SocoEventThread
from .sonos_connector import SonosConnector


class GUIWindow(QtWidgets.QMainWindow):
    system: SonosSystem
    ITEMS_PER_ROW = 10
    ALBUMS_PER_ROW = 6
    ITEM_SCALE = 10
    MARGIN = 5
    _last_selected_track = ""
    _changed_label = None

    def __init__(self):
        super().__init__()
        self.image_cache = {}
        self._library_artwork = None

        self.ui = main_interface.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(os.path.join(BASE_PATH, "icons", "program_icon.png")))
        self.ui.actionBack.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaSkipBackward))
        self.ui.actionPlay_Pause.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.ui.actionStop.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))
        self.ui.actionForward.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaSkipForward))

        self.ui.libraryView.key_press_forward.connect(self.ui.artistFilter.keyPressEvent)
        self.ui.libraryView.key_release_forward.connect(self.ui.artistFilter.keyReleaseEvent)

        self.settings = QtCore.QSettings("Artur Glavic", "Sonos Library Browser")
        self.load_settings()

        self.extend_toolbar()

        self._loghandler = QtLogger(self, self.status_bar)
        logging.getLogger().addHandler(self._loghandler)

        QtCore.QTimer.singleShot(1, self.connect_sonos)

    @QtCore.pyqtSlot()
    def connect_sonos(self):
        self._thread = SonosConnector()
        self._thread.finished.connect(self.sonos_connected)
        self._thread.start()

    @QtCore.pyqtSlot()
    def sonos_connected(self):
        self.system = self._thread.system
        if self.system is None:
            return
        self._thread.wait()
        del self._thread

        self._soco_events = SocoEventThread(self.system.reference)
        self._soco_events.zone_topology_event.connect(self.update_groups)
        self._soco_events.start()

        self.ui.sonosGroupView.set_groups(self.system.groups)
        self.set_playing_group()
        self.ui.sonosGroupView.group_clicked.connect(self.change_active_group)
        self.ui.sonosGroupView.speaker_joined.connect(self.speaker_joined)
        self.ui.sonosGroupView.speaker_unjoined.connect(self.speaker_unjoined)
        self.build_library()

        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.on_timer)
        self._timer.start(1000)

    def speaker_joined(self, speaker_ip: str, group: SonosGroup):
        speaker = None
        for spkr in self.system.speakers:
            if speaker_ip == spkr.ip_address:
                speaker = spkr
                break
        self.status_bar.showMessage(f"Joining {speaker.name} to group {group.label}", 5000)
        speaker.reference.join(group.coordinator)
        QtCore.QTimer.singleShot(5000, self.update_groups)

    def speaker_unjoined(self, speaker_ip: str):
        speaker = None
        for spkr in self.system.speakers:
            if speaker_ip == spkr.ip_address:
                speaker = spkr
                break
        self.status_bar.showMessage(f"Unjoining {speaker.name}", 5000)
        speaker.reference.unjoin()

    def update_groups(self):
        self.ui.sonosGroupView.set_groups(self.system.groups)
        self.set_playing_group()

    def extend_toolbar(self):
        self.status_bar = QtWidgets.QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(5)
        self.status_bar.setSizePolicy(sizePolicy)
        self.ui.toolBar.addWidget(self.status_bar)

        self.progress_bar = QtWidgets.QProgressBar()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(2)
        self.progress_bar.setSizePolicy(sizePolicy)
        self.ui.toolBar.addWidget(self.progress_bar)
        self.ui.toolBar.addWidget(QtWidgets.QLabel("  Volume:"))
        self.volume_control = QtWidgets.QSlider()
        self.volume_control.setOrientation(QtCore.Qt.Horizontal)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        self.volume_control.setSizePolicy(sizePolicy)
        self.volume_control.sliderMoved.connect(self.change_volume)
        self.ui.toolBar.addWidget(self.volume_control)

    def on_timer(self):
        self.update_playing_info()

    def filter_artists(self):
        self.build_library()

    def filtered_artists(self):
        artist_filter = str(self.ui.artistFilter.text()).strip().lower()
        music_library = self.system.speakers[0].reference.music_library
        if len(artist_filter) == 1:
            artists = [
                a for a in music_library.get_album_artists(max_items=1000) if a.title.lower().startswith(artist_filter)
            ]
        else:
            artists = [a for a in music_library.get_album_artists(max_items=1000) if artist_filter in a.title.lower()]
        if self.ui.genreFilter.currentText() != "All Genres":
            filtered_artists = mdb.get_artists(self.ui.genreFilter.currentText())
            artists = [a for a in artists if a.title in filtered_artists]
        artists.sort(key=lambda a: a.title)
        return artists

    def build_library(self):
        music_library = self.system.speakers[0].reference.music_library
        artists = self.filtered_artists()
        self._changed_label = None

        scene = QtWidgets.QGraphicsScene(
            0,
            0,
            self.ui.libraryView.FULL_LIBRARY_WIDTH,
            self.ITEM_SCALE * ((len(artists) - 1) // self.ITEMS_PER_ROW + 1),
        )

        # text labels
        self._artist_labels = {}
        for i, artist in enumerate(artists):
            label = QtWidgets.QGraphicsTextItem()
            label.setHtml(f'<div style="background: rgba(255, 255, 255, 200);"><center>{artist.title}</center></div>')
            label.setPos(self.ITEM_SCALE * (i % self.ITEMS_PER_ROW), self.ITEM_SCALE * (i // self.ITEMS_PER_ROW))
            label.setTextWidth(self.ITEM_SCALE - 2 * self.MARGIN)
            label.setData(QtCore.Qt.UserRole, artist.title)
            label.setZValue(5.0)
            scene.addItem(label)
            self._artist_labels[artist.title] = label

        self.ui.libraryView.setScene(scene)
        scene.mouseReleaseEvent = self.selection_changed
        scene.mouseMoveEvent = self.hover_album
        self.album_scene = scene

        if self._library_artwork is None:
            self.block_library()
            self._last_progress = 0.0
            self.progress_bar.setStatusTip("Loading Albums")
            self.ui.libraryView.verticalScrollBar().setValue(1)

            self._thread = LibraryImageBuilder(music_library, artists)
            self._thread.download_progress.connect(self.update_download)
            self._library_artwork = self._thread.icon_data
            self._thread.start()
        else:
            self.build_artist_icons()

    def block_library(self):
        self.ui.libraryView.blockSignals(True)
        self.ui.artistFilter.blockSignals(True)
        self.ui.iconSizeBox.blockSignals(True)

    def unblock_library(self):
        self.ui.libraryView.blockSignals(False)
        self.ui.artistFilter.blockSignals(False)
        self.ui.iconSizeBox.blockSignals(False)

    @QtCore.pyqtSlot(float)
    def update_download(self, progress):
        self.progress_bar.setValue(int(progress * 100))

        if progress == 1.0:
            self.build_artist_icons(display_range=(self._last_progress, 1.1))
            self._thread.wait()
            del self._thread
            mdb.connect_db()
            self.unblock_library()
            for genre in sorted(mdb.get_genre_list()):
                self.ui.genreFilter.addItem(genre)
            self.progress_bar.setValue(0)
        elif progress > (self._last_progress + 0.1):
            self.build_artist_icons(display_range=(self._last_progress, progress))
            self._last_progress = progress

    def build_artist_icons(self, display_range=None):
        scene: QtWidgets.QGraphicsScene = self.ui.libraryView.scene()
        img_scale = int(self.ITEM_SCALE - 2 * self.MARGIN)
        try:
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(open(os.path.join(BASE_PATH, "icons", "no_artwork.png"), "rb").read())
        except Exception:
            std_icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)
            std_pixmap = std_icon.pixmap(img_scale, img_scale)
        else:
            std_pixmap = pixmap.scaled(img_scale, img_scale, aspectRatioMode=QtCore.Qt.KeepAspectRatio)

        artists = self.filtered_artists()

        # build images
        for i, artist in enumerate(artists):
            if display_range is not None:
                progress = (1 + i) / len(artists)
                if progress < display_range[0]:
                    continue
                elif progress > display_range[1]:
                    break
            if artist.title in self._library_artwork and self._library_artwork[artist.title]:
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(self._library_artwork[artist.title])
                pixmap = pixmap.scaled(img_scale, img_scale, aspectRatioMode=QtCore.Qt.KeepAspectRatio)
            else:
                pixmap = std_pixmap

            item = QtWidgets.QGraphicsPixmapItem()
            item.setPixmap(pixmap)
            item.setPos(
                self.ITEM_SCALE * (i % self.ITEMS_PER_ROW), self.ITEM_SCALE * (i // self.ITEMS_PER_ROW) + self.MARGIN
            )
            item.setData(QtCore.Qt.UserRole, artist.title)

            scene.addItem(item)

    def selection_changed(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        if self.ui.libraryView.signalsBlocked():
            # ignore event if signals are blocked
            return
        scene: QtWidgets.QGraphicsScene = self.ui.libraryView.scene()
        trans = self.ui.libraryView.transform()
        item = scene.itemAt(event.scenePos(), trans)
        if item is None:
            return
        self._last_album_scoll = self.ui.libraryView.verticalScrollBar().value()
        self.show_album(item.data(QtCore.Qt.UserRole))

    def show_album(self, artist):
        albums = list(self.system.speakers[0].reference.music_library.get_albums_for_artist(artist))

        ipr = self.ALBUMS_PER_ROW
        block_width = self.ui.libraryView.FULL_LIBRARY_WIDTH // ipr
        img_scale = int(block_width * 3 / 5)
        img_offset = int(block_width * 1 / 10)

        scene = QtWidgets.QGraphicsScene(
            0,
            0,
            self.ui.libraryView.FULL_LIBRARY_WIDTH,
            block_width * ((len(albums) - 1) // ipr + 1) + block_width * 0.5,
        )

        title = QtWidgets.QGraphicsTextItem(f"Albums by {artist}:")
        title.setPos(10, 5)
        scene.addItem(title)

        album_data = []
        for album in albums:
            img_data, date = mdb.get_image(artist, album.title)
            album_data.append((date, album.title, img_data, album.get_uri()))
        album_data.sort()

        for i, (date, album, img_data, uri) in enumerate(album_data):
            label = QtWidgets.QGraphicsTextItem()
            label.setHtml(f"<center>{album}<br />({date})</center>")
            label.setPos(
                block_width * (i % ipr), block_width * (i // ipr) + img_scale + 2 * self.MARGIN + block_width * 0.25
            )
            label.setTextWidth(block_width * 4 / 5)
            label.setData(QtCore.Qt.UserRole, (artist, album, uri))
            scene.addItem(label)

            if not img_data:
                continue

            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(img_data)
            pixmap = pixmap.scaled(img_scale, img_scale, aspectRatioMode=QtCore.Qt.KeepAspectRatio)

            item = QtWidgets.QGraphicsPixmapItem()
            item.setPixmap(pixmap)
            item.setPos(
                block_width * (i % ipr) + img_offset, block_width * (i // ipr) + self.MARGIN + block_width * 0.25
            )
            item.setData(QtCore.Qt.UserRole, (artist, album, uri))

            scene.addItem(item)

        scene.mouseReleaseEvent = self.select_album
        self.ui.libraryView.setScene(scene)
        self.ui.libraryView.centerOn(title)

    def select_album(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        scene: QtWidgets.QGraphicsScene = self.ui.libraryView.scene()
        trans = self.ui.libraryView.transform()
        item = scene.itemAt(event.scenePos(), trans)
        if item is None:
            self.ui.libraryView.setScene(self.album_scene)
            self.ui.libraryView.verticalScrollBar().setValue(self._last_album_scoll)
            return
        else:
            artist, album, uri = item.data(QtCore.Qt.UserRole)
            group = self.current_group()
            if event.button() == QtCore.Qt.LeftButton:
                group.coordinator.add_uri_to_queue(uri)
                self.status_bar.showMessage(f"Appending {artist} | {album}", 1000)
            elif event.button() == QtCore.Qt.RightButton:
                group.coordinator.clear_queue()
                group.coordinator.add_uri_to_queue(uri)
                group.coordinator.play()
                self.status_bar.showMessage(f"Playing {artist} | {album}", 1000)
            self.update_queue()
            self.update_playing_info()

    def hover_album(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        scene: QtWidgets.QGraphicsScene = self.ui.libraryView.scene()
        trans = self.ui.libraryView.transform()
        item = scene.itemAt(event.scenePos(), trans)
        if item is None:
            if self._changed_label:
                self._changed_label[0].setFont(self._changed_label[1])
                self._changed_label = None
            return
        label = self._artist_labels.get(item.data(QtCore.Qt.UserRole), None)
        if label is None:
            return
        elif self._changed_label:
            if label is self._changed_label[0]:
                return
            else:
                self._changed_label[0].setFont(self._changed_label[1])
                self._changed_label = None
        font: QtGui.QFont = label.font()
        bfont = QtGui.QFont(font)
        bfont.setPointSizeF(bfont.pointSizeF() * 1.5)
        bfont.setBold(True)
        label.setFont(bfont)
        self._changed_label = (label, font)

    def update_queue(self):
        self._last_selected_track = None
        group = self.current_group()
        self.ui.NowPlayingGroup.setText(group.label)

        self.ui.groupQueueList.clear()
        queue = group.coordinator.get_queue()
        player_status = group.coordinator.get_current_transport_info()
        if player_status["current_transport_state"] == "PLAYING":
            self.ui.actionPlay_Pause.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
        else:
            self.ui.actionPlay_Pause.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))

        current_album = ""
        for item in queue:
            item_data = item.to_dict()
            artist = item_data.get("creator", "")
            album = item_data.get("album", "")
            title = item_data.get("title", "")
            if album != current_album:
                current_album = album
                self.ui.groupQueueList.addItem(f"{artist} | {album}")
            self.ui.groupQueueList.addItem(f"\t{title}")
        cur_vol = group.reference.volume
        self.volume_control.setValue(int(cur_vol))

    @QtCore.pyqtSlot()
    def set_playing_group(self):
        # select the first group that is actually playing at th emoment
        for group in self.system.groups:
            player_status = group.coordinator.get_current_transport_info()
            if player_status["current_transport_state"] == "PLAYING":
                self.ui.sonosGroupView.activate_group(group)
                return
        self.ui.sonosGroupView.activate_group(self.system.groups[0])

    def change_active_group(self, group: SonosGroup):
        self.update_queue()
        self.update_playing_info()

    def update_playing_info(self):
        group = self.current_group()
        self.ui.NowPlayingGroup.setText(group.label)

        track = group.now_playing()

        if track.title != self._last_selected_track:
            playing_brush = QtGui.QBrush(QtGui.QColor(100, 200, 100))
            other_brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))

            for i in range(self.ui.groupQueueList.count()):
                item = self.ui.groupQueueList.item(i)
                if item.text() == f"\t{track.title}":
                    item.setBackground(playing_brush)
                else:
                    item.setBackground(other_brush)
            self._last_selected_track = track.title

        self.ui.NowPlayingTrack.setText(track.title)
        self.ui.NowPlayingAlbum.setText(track.album)
        self.ui.NowPlayingArtist.setText(track.artist)
        self.ui.NowPlayingTime.setText(f"{track.position}/{track.duration}")
        if track.album_art == "":
            self.ui.NowPlayingArt.clear()
            return

        if track.album_art not in self.image_cache:
            try:
                data = urllib.request.urlopen(track.album_art).read()
            except Exception:
                log.warning(f"Could not get album art for {track.album_art}", exc_info=True)
                data = None
            self.image_cache[track.album_art] = data
        img_data = self.image_cache[track.album_art]
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(img_data)
        self.ui.NowPlayingArt.setPixmap(pixmap)

    def _set_icon_size(self, index):
        if index == 0:
            self.ITEMS_PER_ROW = 10
            self.ALBUMS_PER_ROW = 6
        elif index == 1:
            self.ITEMS_PER_ROW = 5
            self.ALBUMS_PER_ROW = 3
        elif index == 2:
            self.ITEMS_PER_ROW = 3
            self.ALBUMS_PER_ROW = 2
        total_margins = (self.ITEMS_PER_ROW - 1) * self.MARGIN
        self.ITEM_SCALE = (self.ui.libraryView.FULL_LIBRARY_WIDTH - total_margins) // self.ITEMS_PER_ROW

    @QtCore.pyqtSlot(int)
    def change_icon_size(self, index):
        self._set_icon_size(index)
        self.build_library()

    @QtCore.pyqtSlot()
    def select_speaker(self):
        speaker = self.ui.speakerList.currentItem().data(QtCore.Qt.UserRole).reference
        group = self.ui.groupList.currentItem().data(QtCore.Qt.UserRole).reference
        members = [mi for mi in group.members if mi.is_visible]
        if speaker not in group:
            self.ui.groupToggle.setText("Add")
        elif len(members) == 1:
            self.ui.groupToggle.setText("Sole Member")
        else:
            self.ui.groupToggle.setText("Remove")

    @QtCore.pyqtSlot()
    def toggle_group(self):
        speaker: SonosSpeaker = self.ui.speakerList.currentItem().data(QtCore.Qt.UserRole)
        group: SonosGroup = self.ui.groupList.currentItem().data(QtCore.Qt.UserRole)
        members = [mi for mi in group.reference.members if mi.is_visible]
        if speaker.reference not in group.reference:
            self.status_bar.showMessage(f"Joining {speaker.name} with {group.label}", 1000)
            speaker.join(group.coordinator)
        elif len(members) == 1:
            return
        else:
            self.status_bar.showMessage(f"Removing {speaker.name} from {group.label}", 1000)
            speaker.unjoin()
        QtCore.QTimer.singleShot(1000, self.build_group_list)

    @QtCore.pyqtSlot()
    def queue_play_pause(self):
        group = self.current_group()

        player_status = group.coordinator.get_current_transport_info()
        if player_status["current_transport_state"] == "PLAYING":
            group.coordinator.pause()
            self.ui.actionPlay_Pause.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
            self.status_bar.showMessage(f"Pausing on {group.label}", 1000)
        else:
            group.coordinator.play()
            self.ui.actionPlay_Pause.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
            self.status_bar.showMessage(f"Playing on {group.label}", 1000)

    @QtCore.pyqtSlot()
    def queue_stop(self):
        group: SonosGroup = self.current_group()
        group.coordinator.stop()
        self.status_bar.showMessage(f"Stop playing on {group.label}", 1000)

    @QtCore.pyqtSlot()
    def queue_prev(self):
        group = self.current_group()
        group.coordinator.previous()
        self.status_bar.showMessage(f"Playing previeous song on {group.label}", 1000)

    @QtCore.pyqtSlot()
    def queue_next(self):
        group = self.current_group()
        group.coordinator.next()
        self.status_bar.showMessage(f"Playing next song on {group.label}", 1000)

    @QtCore.pyqtSlot(int)
    def change_volume(self, value):
        group = self.current_group()
        group.reference.volume = value

    def current_group(self):
        return self.ui.sonosGroupView.current_group

    def load_settings(self):
        self._set_icon_size(self.settings.value("mainWindow/icon_size", 0))
        self.ui.iconSizeBox.blockSignals(True)
        self.ui.iconSizeBox.setCurrentIndex(self.settings.value("mainWindow/icon_size", 0))
        self.ui.iconSizeBox.blockSignals(False)
        if self.settings.value("mainWindow/geometry") is not None:
            self.restoreGeometry(self.settings.value("mainWindow/geometry"))
            self.restoreState(self.settings.value("mainWindow/state"))

    def closeEvent(self, event: QtGui.QCloseEvent):
        self._soco_events.quit()
        if getattr(self, "_thread", None):
            self._thread.quit()
            self._thread.wait()
        self._soco_events.wait()
        self.settings.setValue("mainWindow/geometry", self.saveGeometry())
        self.settings.setValue("mainWindow/state", self.saveState())
        self.settings.setValue("mainWindow/icon_size", self.ui.iconSizeBox.currentIndex())
        super().closeEvent(event)
