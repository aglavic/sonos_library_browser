"""
A Widget to add random album to queue.

Users can choose to restrict the choice to certain genres and modify
the probability of each genre to be chosen.
(Full probability of all genres corresponds to the full random choice,
meaning the genres are weighted by the number of albums they contain.)
"""

import random

from PyQt5.QtCore import Qt, pyqtSignal, QSettings
from PyQt5.QtWidgets import QWidget, QCheckBox, QHBoxLayout, QSlider, QVBoxLayout

from . import music_library as mdb
from . random_pools_interface import Ui_RandomPools

class GenreController(QWidget):
    def __init__(self, parent=None, title='genre'):
        super().__init__(parent=parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)


        self.used = QCheckBox()
        self.used.setText(title)

        self.probability = QSlider(Qt.Horizontal)
        self.probability.setMinimum(1)
        self.probability.setMaximum(100)
        self.probability.setValue(100)

        layout.addWidget(self.used)
        layout.addWidget(self.probability)


class RandomPoolWidget(QWidget):
    append_random_album = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_RandomPools()
        self.ui.setupUi(self)

    def set_genres(self, genres):
        glayout=QVBoxLayout(self.ui.genreControls)
        glayout.setContentsMargins(0, 0, 0, 0)
        self.ui.genreControls.setLayout(glayout)
        self.genres = {}
        for genre in genres:
            g = GenreController(self.ui.genreControls, genre)
            glayout.addWidget(g)
            self.genres[genre] = g
        self.ui.addRandomButton.pressed.connect(self.get_random_choice)

    def get_random_choice(self):
        # get a random album from the database
        if self.ui.genreCheckbox.isChecked():
            # choose by gener
            choice_lists = {}
            for genre, ctrl in self.genres.items():
                if ctrl.used.isChecked():
                    choice_lists[genre] = mdb.get_albums(genre)
            total_albums = sum([len(gl) for gl in choice_lists.values()])
            probabilities = []
            total_proab = 0.
            for genre, gl in choice_lists.items():
                defprob = len(gl)/total_albums
                defprob*= self.genres[genre].probability.value()/100.
                probabilities.append((genre, defprob))
                total_proab+=defprob
            rnd = random.random()*total_proab
            for genre, defprob in probabilities:
                if rnd>defprob:
                    rnd-=defprob
                else:
                    genre_albums = choice_lists[genre]
                    choice = random.randrange(0, len(genre_albums))
                    artist, album = genre_albums[choice]
                    break
        else:
            all_albums = mdb.get_albums()
            choice = random.randrange(0, len(all_albums))
            artist, album = all_albums[choice]
        self.append_random_album.emit(artist, album)

    def save_settings(self, settings:QSettings):
        settings.setValue("randomPools/autoadd", int(self.ui.autoAddAlbums.isChecked()))
        settings.setValue("randomPools/autotracks", self.ui.titlesLeftSetting.value())
        settings.setValue("randomPools/usegenres", int(self.ui.genreCheckbox.isChecked()))
        for genre, widget in self.genres.items():
            settings.setValue(f"randomPools/{genre}/active", int(widget.used.isChecked()))
            settings.setValue(f"randomPools/{genre}/probability", widget.probability.value())

    def load_settings(self, settings:QSettings):
        self.ui.autoAddAlbums.setChecked(bool(settings.value("randomPools/autoadd", False)))
        self.ui.titlesLeftSetting.setValue(settings.value("randomPools/autotracks", 1))
        self.ui.genreCheckbox.setChecked(bool(settings.value("randomPools/usegenres", False)))
        for genre, widget in self.genres.items():
            widget.used.setChecked(bool(settings.value(f"randomPools/{genre}/active", False)))
            widget.probability.setValue(settings.value(f"randomPools/{genre}/probability", 100))
