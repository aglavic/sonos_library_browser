"""
A graphical representation of Sonos Groups that allows a drag and drop of
speaker items from one group to the other or to unjoin.
"""

import os

from math import cos, pi, sin

from PyQt5 import QtCore, QtGui, QtWidgets

from . import BASE_PATH


class SonosGroupWidget(QtWidgets.QGraphicsView):
    FULL_WIDGET_SCALE = 500
    MARGIN = 5
    orientation = "vertical"
    group_items: list[QtWidgets.QGraphicsItem]

    def __init__(self, parent):
        super().__init__(parent)
        pixmap = QtGui.QPixmap()
        pixmap.load(os.path.join(BASE_PATH, "icons", "no_artwork.png"))
        pixmap = pixmap.scaled(80, 50, aspectRatioMode=QtCore.Qt.KeepAspectRatio)

        spkr1 = QtWidgets.QGraphicsPixmapItem(pixmap)
        spkr2 = QtWidgets.QGraphicsPixmapItem(pixmap)
        spkr3 = QtWidgets.QGraphicsPixmapItem(pixmap)
        spkr4 = QtWidgets.QGraphicsPixmapItem(pixmap)
        self.group_items = [SonosGroupGraphics("bier", [spkr1]), SonosGroupGraphics("hier", [spkr2, spkr3, spkr4])]
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.draw_items()

    def resizeEvent(self, QResizeEvent):
        #
        w = self.width() - self.verticalScrollBar().width()
        h = self.height() - self.horizontalScrollBar().height()

        if w > (1.5 * h):
            s = h / self.FULL_WIDGET_SCALE
            if self.orientation == "vertical":
                self.orientation = "horizontal"
                self.draw_items()
        else:
            s = w / self.FULL_WIDGET_SCALE
            if self.orientation == "horizontal":
                self.orientation = "vertical"
                self.draw_items()
        T = QtGui.QTransform(s, 0.0, 0.0, s, 0.0, 0.0)
        self.setTransform(T)

    def draw_items(self):
        litm = len(self.group_items)
        if self.orientation == "horizontal":
            w = litm * self.FULL_WIDGET_SCALE + (litm - 1) * self.MARGIN
            h = self.FULL_WIDGET_SCALE * 0.8
        else:
            h = litm * self.FULL_WIDGET_SCALE * 0.8 + (litm - 1) * self.MARGIN
            w = self.FULL_WIDGET_SCALE
        scene = QtWidgets.QGraphicsScene(0, 0, w, h)
        for group in self.group_items:
            scene.addItem(group)
        self.setScene(scene)
        self.position_items()

    def position_items(self):
        if self.orientation == "horizontal":
            dpos = (self.FULL_WIDGET_SCALE + self.MARGIN, 0)
        else:
            dpos = (0, self.FULL_WIDGET_SCALE * 0.8 + self.MARGIN)
        for i, group in enumerate(self.group_items):
            group.setPos(dpos[0] * i, dpos[1] * i)


class SonosGroupGraphics(QtWidgets.QGraphicsEllipseItem):
    speakers: list[QtWidgets.QGraphicsItem]

    def __init__(self, title, speakers):
        super().__init__(
            SonosGroupWidget.FULL_WIDGET_SCALE * 0.15,
            SonosGroupWidget.FULL_WIDGET_SCALE * 0.1,
            SonosGroupWidget.FULL_WIDGET_SCALE * 0.7,
            SonosGroupWidget.FULL_WIDGET_SCALE * 0.5,
        )
        gradient = QtGui.QRadialGradient(0.55, 0.4, 0.65)
        gradient.setCoordinateMode(QtGui.QGradient.ObjectMode)
        gradient.setColorAt(0.0, QtGui.QColor(150, 50, 50))
        gradient.setColorAt(1.0, QtGui.QColor(50, 0, 0))
        self.setBrush(gradient)

        self.title = QtWidgets.QGraphicsTextItem(title)
        font: QtGui.QFont = self.title.font()
        font.setPointSizeF(30.0)
        font.setBold(True)
        self.title.setFont(font)
        self.title.setDefaultTextColor(QtGui.QColor(255, 255, 255))
        tc = self.title.boundingRect().width() / 2.0
        self.title.setParentItem(self)
        self.title.setPos(
            SonosGroupWidget.FULL_WIDGET_SCALE * 0.5 - tc, SonosGroupWidget.FULL_WIDGET_SCALE * 0.35 - 15.0
        )

        self.speakers = speakers
        self.position_speakers()

    def position_speakers(self):
        lsp = len(self.speakers)
        cx = SonosGroupWidget.FULL_WIDGET_SCALE * 0.5
        cy = SonosGroupWidget.FULL_WIDGET_SCALE * 0.35
        rx = SonosGroupWidget.FULL_WIDGET_SCALE * 0.3
        ry = SonosGroupWidget.FULL_WIDGET_SCALE * 0.25
        for i, spkr in enumerate(self.speakers):
            spkr.setParentItem(self)
            phi = 2 * pi * i / lsp
            x = cx + sin(phi) * rx - spkr.boundingRect().width() / 2.0
            y = cy - cos(phi) * ry - spkr.boundingRect().height() / 2.0
            spkr.setPos(x, y)
            spkr.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
