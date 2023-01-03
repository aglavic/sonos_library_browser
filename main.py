import sys
import urllib.request
from dataclasses import dataclass, fields
from time import sleep

import soco
import soco.groups
import soco.data_structures
import eyed3

from OpenGL import GL
from PyQt5 import QtCore, QtGui, QtWidgets

import main_interface
import music_library as mdb

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
            last_date = -1
            albums = music_library.get_albums_for_artist(artist.title)
            for album in albums:
                try:
                    img_data, date = mdb.get_image(artist.title, album.title)
                    if not img_data:
                        rtrack = music_library.get_tracks_for_album(artist.title, album.title, full_album_art_uri=True).pop()
                        uri = music_library.build_album_art_full_uri(rtrack.album_art_uri)
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
    ITEM_SCALE = 200

    def __init__(self):
        super().__init__()
        self.image_cache = {}
        self.ui = main_interface.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setup_sonos()
        self.progress_bar = QtWidgets.QProgressBar()
        self.ui.toolBar.addWidget(self.progress_bar)

        self.build_group_list()
        self.build_library()

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

    def build_group_list(self):
        self.ui.groupList.clear()
        for i, item in enumerate(self.system.groups):
            self.ui.groupList.addItem(item.label)
        self.ui.groupList.setCurrentRow(0)

    def build_library(self):
        music_library=self.system.speakers[0].reference.music_library
        artists = list(music_library.get_album_artists(max_items=1000))
        artists.sort(key=lambda a: a.title)

        scene = QtWidgets.QGraphicsScene(0, 0, self.ITEM_SCALE*self.ITEMS_PER_ROW,
                                         self.ITEM_SCALE*(len(artists)//self.ITEMS_PER_ROW+1))

        labels = {}
        # text labels
        for i, artist in enumerate(artists):
            label=QtWidgets.QGraphicsTextItem(artist.title)
            label.setPos(self.ITEM_SCALE*(i%self.ITEMS_PER_ROW),
                         self.ITEM_SCALE*(i//self.ITEMS_PER_ROW)+self.ITEM_SCALE*2/3)
            label.setTextWidth(self.ITEM_SCALE*3/5)
            label.setData(0, artist.title)
            scene.addItem(label)

        self.ui.libraryView.setScene(scene)

        self._image_builder = LibraryImageBuilder(music_library, artists)
        self._image_builder.download_progress.connect(self.update_download)

        self._thread = QtCore.QThread()
        self._image_builder.moveToThread(self._thread)
        self.progress_bar.setStatusTip('Loading Albums')
        self._thread.started.connect(self._image_builder.build_library_images)
        self._thread.start()

    def update_download(self, progress):
        self.progress_bar.setValue(int(progress*100))

        if progress == 1.0:
            icon_data = self._image_builder.icon_data
            for i, artist in enumerate(self._image_builder.artists):
                pass

            scene:QtWidgets.QGraphicsScene = self.ui.libraryView.scene()
            img_scale = int(self.ITEM_SCALE * 3 / 5)
            std_icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)
            std_pixmap = std_icon.pixmap(img_scale, img_scale)
            # build images
            for i, artist in enumerate(self._image_builder.artists):
                if artist.title in icon_data:
                    pixmap = QtGui.QPixmap()
                    pixmap.loadFromData(icon_data[artist.title])
                    pixmap = pixmap.scaled(img_scale, img_scale,
                                           aspectRatioMode=QtCore.Qt.KeepAspectRatio)
                else:
                    pixmap = std_pixmap

                item = QtWidgets.QGraphicsPixmapItem()
                item.setPixmap(pixmap)
                item.setPos(self.ITEM_SCALE * (i % self.ITEMS_PER_ROW),
                            self.ITEM_SCALE * (i // self.ITEMS_PER_ROW)+5)
                item.setData(0, artist.title)

                scene.addItem(item)

            scene.mouseReleaseEvent = self.selection_changed
            del(self._image_builder)
            self._thread.quit()
            self._thread.wait()
            del(self._thread)
            mdb.connect_db()

    def selection_changed(self, event:QtWidgets.QGraphicsSceneMouseEvent):
        scene: QtWidgets.QGraphicsScene = self.ui.libraryView.scene()
        trans = self.ui.libraryView.transform()
        item = scene.itemAt(event.scenePos(), trans)
        if item is None:
            return
        self.show_album(item.data(0))

    def show_album(self, artist):
        albums = list(self.system.speakers[0].reference.music_library.get_albums_for_artist(artist))

        width = min(self.ITEM_SCALE * self.ITEMS_PER_ROW, self.ITEM_SCALE*len(albums))
        scene = QtWidgets.QGraphicsScene(0, 0, width,
                            self.ITEM_SCALE * (len(albums) // self.ITEMS_PER_ROW + 1)+self.ITEM_SCALE*0.5)

        title = QtWidgets.QGraphicsTextItem(f'Albums by {artist}:')
        title.setPos(10, 5)
        scene.addItem(title)

        img_scale = int(self.ITEM_SCALE * 3 / 5)
        album_data = []
        for album in albums:
            img_data, date = mdb.get_image(artist, album.title)
            album_data.append((date, album.title, img_data, album.get_uri()))
        album_data.sort()

        for i, (date, album, img_data, uri) in enumerate(album_data):
            label = QtWidgets.QGraphicsTextItem(f'{album} ({date})')
            label.setPos(self.ITEM_SCALE*(i%self.ITEMS_PER_ROW),
                         self.ITEM_SCALE*(i//self.ITEMS_PER_ROW)+self.ITEM_SCALE*2/3+self.ITEM_SCALE*0.5)
            label.setTextWidth(self.ITEM_SCALE*3/5)
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
            item.setPos(self.ITEM_SCALE * (i % self.ITEMS_PER_ROW),
                        self.ITEM_SCALE * (i // self.ITEMS_PER_ROW) + 5+self.ITEM_SCALE*0.5)
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
            self.build_library()
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
        queue = gi.coordinator.get_queue()
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
            data = urllib.request.urlopen(track.album_art).read()
            self.image_cache[track.album_art] = data
        img_data = self.image_cache[track.album_art]
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(img_data)
        self.ui.NowPlayingArt.setPixmap(pixmap)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
