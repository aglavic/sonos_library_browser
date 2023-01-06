import sys
import os
import urllib.request
from dataclasses import dataclass, fields

import soco
import soco.groups
import soco.data_structures
import eyed3

from PyQt5 import QtCore, QtGui, QtWidgets

import main_interface
import music_library as mdb

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
SPEAKER_ICONS = {
    #'Sonos Ray': os.path.join(BASE_PATH, 'icons', 'move.png'),
    #'Sonos Beam': os.path.join(BASE_PATH, 'icons', 'move.png'),
    'Sonos Move': os.path.join(BASE_PATH, 'icons', 'move.png'),
    #'Sonos Port': os.path.join(BASE_PATH, 'icons', 'move.png'),
    }


@dataclass
class Track:
    artist: str
    album: str
    title: str
    position: str
    duration: str
    album_art: str
    uri: str

    @classmethod
    def from_dict(cls, env):
        flds = [f.name for f in fields(cls)]
        return cls(**{
            k: v for k, v in env.items()
            if k in flds
        })

@dataclass
class SonosSpeaker:
    ip_address: str
    name: str
    room: str
    reference: soco.SoCo

@dataclass
class SonosGroup:
    label: str
    coordinator: soco.SoCo
    reference: soco.groups.ZoneGroup

    def now_playing(self) -> Track:
        return Track.from_dict(self.coordinator.get_current_track_info())

@dataclass
class SonosSystem:
    speakers: list[SonosSpeaker]

    @property
    def reference(self)->soco.SoCo:
        return self.speakers[0].reference.group.coordinator

    @property
    def groups(self)->list[SonosGroup]:
        out = []
        for item in self.reference.all_groups:
            group=SonosGroup(item.short_label, item.coordinator, item)
            out.append(group)
        return out

    def now_playing(self):
        for g in self.groups:
            t = g.now_playing()
            #print(f'{g.label}: {t}')

def main():
    app = QtWidgets.QApplication([])
    win = GUIWindow()
    win.show()
    sys.exit(app.exec())


class LibraryImageBuilder(QtCore.QObject):

    def __init__(self, music_library, artists):
        super().__init__()
        self.music_library = music_library
        self.artists = artists

    def build_library_images(self):
        mdb.connect_db()
        music_library = self.music_library
        artists = self.artists

        # collect icons
        self.icon_data={}
        for i, artist in enumerate(artists):
            img_data, date = mdb.get_last_image(artist.title)
            if img_data is not None:
                self.icon_data[artist.title] = img_data
            else:
                last_date = -1
                albums = music_library.get_albums_for_artist(artist.title)
                for album in albums:
                    try:
                        img_data, date = mdb.get_image(artist.title, album.title)
                        if not img_data:
                            rtrack = music_library.get_tracks_for_album(artist.title, album.title,
                                                                        full_album_art_uri=True).pop()
                            uri = rtrack.album_art_uri
                            rtfile = rtrack.get_uri()
                            if rtfile.startswith('x-file-cifs:'):
                                rtpath = urllib.request.unquote(rtfile.split(':',1)[1])
                                rmp3 = eyed3.load(rtpath)

                    except Exception as e:
                        print(e)
                    else:
                        if not img_data:
                            try:
                                img_data = urllib.request.urlopen(uri).read()
                            except Exception as e:
                                print(e)
                            else:
                                try:
                                    date = int(str(rmp3.tag.recording_date))
                                except ValueError:
                                    date = 0
                                mdb.insert_image(artist.title, album.title, img_data, date)
                        if date>last_date:
                            self.icon_data[artist.title] = img_data
                            last_date = date
            self.download_progress.emit((i+1)/len(artists))
        print('Thread finished')

    download_progress = QtCore.pyqtSignal(float)


class GUIWindow(QtWidgets.QMainWindow):
    system: SonosSystem
    ITEMS_PER_ROW = 10
    ALBUMS_PER_ROW = 6
    ITEM_SCALE = 10
    MARGIN = 5

    def __init__(self):
        super().__init__()
        self.image_cache = {}
        self.ui = main_interface.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.actionBack.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaSkipBackward))
        self.ui.actionPlay_Pause.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.ui.actionStop.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))
        self.ui.actionForward.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaSkipForward))

        self.setup_sonos()
        self.progress_bar = QtWidgets.QProgressBar()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(3)
        self.progress_bar.setSizePolicy(sizePolicy)
        self.ui.toolBar.addWidget(self.progress_bar)
        self.ui.toolBar.addWidget(QtWidgets.QLabel('  Volume:'))
        self.volume_control = QtWidgets.QSlider()
        self.volume_control.setOrientation(QtCore.Qt.Horizontal)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        self.volume_control.setSizePolicy(sizePolicy)
        self.volume_control.sliderMoved.connect(self.change_volume)
        self.ui.toolBar.addWidget(self.volume_control)

        self.build_speaker_list()
        self.build_group_list()
        self._library_artwork = None
        # calculate item scale and build library
        self.change_icon_size(self.ui.iconSizeBox.currentIndex())

        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.on_timer)
        self._timer.start(1000)

    def on_timer(self):
        self.update_playing_info(self.ui.groupList.currentRow())

    def setup_sonos(self):
        speakers = []
        for item in soco.discover():
            si = item.get_speaker_info()
            speaker = SonosSpeaker(item.ip_address,
                                   si['model_name'],
                                   si['zone_name'],
                                   item
                                   )
            speakers.append(speaker)
        system = SonosSystem(speakers)
        system.now_playing()
        self.system = system

    def build_speaker_list(self):
        self.ui.speakerList.clear()
        for i, item in enumerate(self.system.speakers):
            self.ui.speakerList.addItem(f'{item.name} ({item.ip_address})\n\t{item.room}')
            speaker_type = item.reference.speaker_info.get('model_name', None)


    def build_group_list(self):
        self.ui.groupList.clear()
        for i, item in enumerate(self.system.groups):
            self.ui.groupList.addItem(item.label)
        self.ui.groupList.setCurrentRow(0)

    def build_library(self):
        music_library=self.system.speakers[0].reference.music_library
        artists = list(music_library.get_album_artists(max_items=1000))
        artists.sort(key=lambda a: a.title)

        scene = QtWidgets.QGraphicsScene(0, 0, self.ui.libraryView.FULL_LIBRARY_WIDTH,
                                         self.ITEM_SCALE*(len(artists)//self.ITEMS_PER_ROW+1))

        labels = {}
        # text labels
        for i, artist in enumerate(artists):
            label=QtWidgets.QGraphicsTextItem()
            label.setHtml(f'<div style="background: rgba(255, 255, 255, 200);"><center>{artist.title}</center></div>')
            label.setPos(self.ITEM_SCALE*(i%self.ITEMS_PER_ROW),
                         self.ITEM_SCALE*(i//self.ITEMS_PER_ROW))
            label.setTextWidth(self.ITEM_SCALE-2*self.MARGIN)
            label.setData(0, artist.title)
            label.setZValue(5.0)
            scene.addItem(label)

        self.ui.libraryView.setScene(scene)

        if self._library_artwork is None:
            self._image_builder = LibraryImageBuilder(music_library, artists)
            self._image_builder.download_progress.connect(self.update_download)

            self._thread = QtCore.QThread()
            self._image_builder.moveToThread(self._thread)
            self.progress_bar.setStatusTip('Loading Albums')
            self._thread.started.connect(self._image_builder.build_library_images)
            self._thread.start()
        else:
            self.build_artist_icons()

    def update_download(self, progress):
        self.progress_bar.setValue(int(progress*100))

        if progress == 1.0:
            self._library_artwork = self._image_builder.icon_data
            self.build_artist_icons()
            del(self._image_builder)
            self._thread.quit()
            self._thread.wait()
            del(self._thread)
            mdb.connect_db()

    def build_artist_icons(self):
        scene: QtWidgets.QGraphicsScene = self.ui.libraryView.scene()
        img_scale = int(self.ITEM_SCALE - 2 * self.MARGIN)
        std_icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)
        std_pixmap = std_icon.pixmap(img_scale, img_scale)

        music_library=self.system.speakers[0].reference.music_library
        artists = list(music_library.get_album_artists(max_items=1000))
        artists.sort(key=lambda a: a.title)

        # build images
        for i, artist in enumerate(artists):
            if artist.title in self._library_artwork:
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(self._library_artwork[artist.title])
                pixmap = pixmap.scaled(img_scale, img_scale,
                                       aspectRatioMode=QtCore.Qt.KeepAspectRatio)
            else:
                pixmap = std_pixmap

            item = QtWidgets.QGraphicsPixmapItem()
            item.setPixmap(pixmap)
            item.setPos(self.ITEM_SCALE * (i % self.ITEMS_PER_ROW),
                        self.ITEM_SCALE * (i // self.ITEMS_PER_ROW) + self.MARGIN)
            item.setData(0, artist.title)

            scene.addItem(item)
        scene.mouseReleaseEvent = self.selection_changed
        self.album_scene = scene

    def selection_changed(self, event:QtWidgets.QGraphicsSceneMouseEvent):
        scene: QtWidgets.QGraphicsScene = self.ui.libraryView.scene()
        trans = self.ui.libraryView.transform()
        item = scene.itemAt(event.scenePos(), trans)
        if item is None:
            return
        self._last_album_scoll = self.ui.libraryView.verticalScrollBar().value()
        self.show_album(item.data(0))

    def show_album(self, artist):
        albums = list(self.system.speakers[0].reference.music_library.get_albums_for_artist(artist))

        ipr = self.ALBUMS_PER_ROW
        block_width = self.ui.libraryView.FULL_LIBRARY_WIDTH//ipr

        scene = QtWidgets.QGraphicsScene(0, 0, self.ui.libraryView.FULL_LIBRARY_WIDTH,
                            2*self.ITEM_SCALE * (len(albums) // ipr + 1)+self.ITEM_SCALE*0.5)

        title = QtWidgets.QGraphicsTextItem(f'Albums by {artist}:')
        title.setPos(10, 5)
        scene.addItem(title)

        img_scale = int(block_width * 3 / 5)
        img_offset = int(block_width * 1 / 10)
        album_data = []
        for album in albums:
            img_data, date = mdb.get_image(artist, album.title)
            album_data.append((date, album.title, img_data, album.get_uri()))
        album_data.sort()

        for i, (date, album, img_data, uri) in enumerate(album_data):
            label = QtWidgets.QGraphicsTextItem()
            label.setHtml(f'<center>{album}<br />({date})</center>')
            label.setPos(block_width*(i%ipr),
                         block_width*(i//ipr)+img_scale+2*self.MARGIN+block_width*0.25)
            label.setTextWidth(block_width*4/5)
            label.setData(0, (artist, album, uri))
            scene.addItem(label)

            if img_data is None:
                continue

            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(img_data)
            pixmap = pixmap.scaled(img_scale, img_scale,
                                   aspectRatioMode=QtCore.Qt.KeepAspectRatio)

            item = QtWidgets.QGraphicsPixmapItem()
            item.setPixmap(pixmap)
            item.setPos(block_width * (i % ipr) + img_offset,
                        block_width * (i // ipr) + self.MARGIN+block_width*0.25)
            item.setData(0, (artist, album, uri))

            scene.addItem(item)

        scene.mouseReleaseEvent=self.select_album
        self.ui.libraryView.setScene(scene)
        self.ui.libraryView.centerOn(title)


    def select_album(self, event:QtWidgets.QGraphicsSceneMouseEvent):
        scene: QtWidgets.QGraphicsScene = self.ui.libraryView.scene()
        trans = self.ui.libraryView.transform()
        item = scene.itemAt(event.scenePos(), trans)
        if item is None:
            self.ui.libraryView.setScene(self.album_scene)
            self.ui.libraryView.verticalScrollBar().setValue(self._last_album_scoll)
            return
        else:
            artist, album, uri = item.data(0)
            glabel = self.ui.groupList.currentItem().text()
            group = None
            for gi in self.system.groups:
                if gi.label == glabel:
                    group = gi
                    break
            if group is None:
                return
            else:
                if event.button() == QtCore.Qt.LeftButton:
                    group.coordinator.add_uri_to_queue(uri)
                elif event.button() == QtCore.Qt.RightButton:
                    group.coordinator.clear_queue()
                    group.coordinator.add_uri_to_queue(uri)
                    group.coordinator.play()
                self.update_queue(self.ui.groupList.currentRow())
                self.update_playing_info(self.ui.groupList.currentRow())

    def update_playing(self, index):
        glabel = self.ui.groupList.item(index).text()
        self.ui.NowPlayingGroup.setText(glabel)
        group = None
        for gi in self.system.groups:
            if gi.label==glabel:
                group = gi
                break
        if group is None:
            self.build_group_list()
            return
        self.update_queue(index)
        self.update_playing_info(index)

    def update_queue(self, index):
        glabel = self.ui.groupList.item(index).text()
        self.ui.NowPlayingGroup.setText(glabel)
        group = None
        for gi in self.system.groups:
            if gi.label==glabel:
                group = gi
                break
        queue = group.coordinator.get_queue()
        player_status = group.coordinator.get_current_transport_info()
        if player_status['current_transport_state'] == 'PLAYING':
            self.ui.actionPlay_Pause.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
        else:
            self.ui.actionPlay_Pause.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.ui.groupQueueList.clear()
        current_album = ''
        for item in queue:
            item_data=item.to_dict()
            artist = item_data.get('creator', '')
            album = item_data.get('album', '')
            title = item_data.get('title', '')
            if album != current_album:
                current_album = album
                self.ui.groupQueueList.addItem(f'{artist} | {album}')
            self.ui.groupQueueList.addItem(f'\t{item.title}')
        self.ui.groupQueueList.setCurrentRow(0)
        cur_vol = group.coordinator.volume
        self.volume_control.setValue(int(cur_vol))

    def update_playing_info(self, index):
        glabel = self.ui.groupList.item(index).text()
        self.ui.NowPlayingGroup.setText(glabel)
        group = None
        for gi in self.system.groups:
            if gi.label==glabel:
                group = gi
                break
        if group is None:
            self.build_group_list()
            return

        track = group.now_playing()

        if self.ui.groupQueueList.currentItem().text()!=f'\t{track.title}':
            for i in range(self.ui.groupQueueList.count()):
                if self.ui.groupQueueList.item(i).text()==f'\t{track.title}':
                    self.ui.groupQueueList.setCurrentRow(i)
                    break

        self.ui.NowPlayingTrack.setText(track.title)
        self.ui.NowPlayingAlbum.setText(track.album)
        self.ui.NowPlayingArtist.setText(track.artist)
        self.ui.NowPlayingTime.setText(f'{track.position}/{track.duration}')
        if track.album_art=='':
            self.ui.NowPlayingArt.clear()
            return

        if track.album_art not in self.image_cache:
            try:
                data = urllib.request.urlopen(track.album_art).read()
            except Exception as e:
                print(e)
                data = None
            self.image_cache[track.album_art] = data
        img_data = self.image_cache[track.album_art]
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(img_data)
        self.ui.NowPlayingArt.setPixmap(pixmap)

    def change_icon_size(self, index):
        if index==0:
            self.ITEMS_PER_ROW=10
            self.ALBUMS_PER_ROW=6
        elif index==1:
            self.ITEMS_PER_ROW=5
            self.ALBUMS_PER_ROW=3
        elif index==2:
            self.ITEMS_PER_ROW=3
            self.ALBUMS_PER_ROW=2
        total_margins = (self.ITEMS_PER_ROW-1)*self.MARGIN
        self.ITEM_SCALE = (self.ui.libraryView.FULL_LIBRARY_WIDTH-total_margins)//self.ITEMS_PER_ROW
        self.build_library()

    def queue_play_pause(self):
        group = self.current_group()

        player_status = group.coordinator.get_current_transport_info()
        if player_status['current_transport_state'] == 'PLAYING':
            group.coordinator.pause()
            self.ui.actionPlay_Pause.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        else:
            group.coordinator.play()
            self.ui.actionPlay_Pause.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))

    def queue_stop(self):
        group = self.current_group()
        group.coordinator.stop()

    def queue_prev(self):
        group = self.current_group()
        group.coordinator.previous()

    def queue_next(self):
        group = self.current_group()
        group.coordinator.next()

    def change_volume(self, value):
        group = self.current_group()
        group.coordinator.volume=value


    def current_group(self):
        glabel = self.ui.groupList.currentItem().text()
        self.ui.NowPlayingGroup.setText(glabel)
        group = None
        for gi in self.system.groups:
            if gi.label == glabel:
                group = gi
                break
        return group


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
