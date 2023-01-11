"""
A graphical representation of Sonos Groups that allows a drag and drop of
speaker items from one group to the other or to unjoin.
"""

import os

from math import cos, pi, sin

from PyQt5 import QtCore, QtGui, QtWidgets

from . import BASE_PATH
from .data_model import SonosGroup, SonosSpeaker


class SonosGroupWidget(QtWidgets.QGraphicsView):
    FULL_WIDGET_SCALE = 500
    MARGIN = 5
    orientation = "vertical"
    group_items: list[QtWidgets.QGraphicsItem]
    current_group: SonosGroup = None

    group_clicked = QtCore.pyqtSignal(SonosGroup)
    speaker_joined = QtCore.pyqtSignal(str, SonosGroup)
    speaker_unjoined = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.setAcceptDrops(True)

        self.group_items = []
        self.setRenderHint(QtGui.QPainter.Antialiasing)

    def set_groups(self, groups: list[SonosGroup]):
        glist = [(g.label, g) for g in groups]
        glist.sort()
        self.group_items = []
        for label, group in glist:
            gg = SonosGroupGraphics(self, group)
            self.group_items.append(gg)
        self.draw_items()

    def dragMoveEvent(self, event: QtGui.QDropEvent):
        event.setAccepted(True)

    def dragEnterEvent(self, event: QtWidgets.QGraphicsSceneDragDropEvent):
        mime: QtCore.QMimeData = event.mimeData()
        if mime.hasFormat("text/sonos_ip"):
            event.setAccepted(True)
        else:
            event.setAccepted(False)

    def dropEvent(self, event: QtGui.QDropEvent):
        child: SonosGroupGraphics = self.itemAt(event.pos())
        speaker_ip = bytes(event.mimeData().data("text/sonos_ip")).decode("utf-8")
        if child is None:
            self.speaker_unjoined.emit(speaker_ip)
        else:
            while not isinstance(child, SonosGroupGraphics):
                child = child.parentItem()
            sids = [s.speaker.ip_address for s in child.speakers]
            if speaker_ip in sids:
                event.setAccepted(False)
                return
            self.speaker_joined.emit(speaker_ip, child.group)
        event.setAccepted(True)

    def activate_group(self, group: SonosGroup):
        for gg in self.group_items:
            if gg.group == group:
                gg.activate_group()
            else:
                gg.deactivate_group()
        self.current_group = group
        self.group_clicked.emit(group)

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
            scene.dragEnterEvent = group.dragEnterEvent
        self.setScene(scene)
        self.position_items()

    def position_items(self):
        if self.orientation == "horizontal":
            dpos = (self.FULL_WIDGET_SCALE + self.MARGIN, 0)
        else:
            dpos = (0, self.FULL_WIDGET_SCALE * 0.8 + self.MARGIN)
        for i, group in enumerate(self.group_items):
            group.setPos(dpos[0] * i, dpos[1] * i)


class SonosSpeakerGraphics(QtWidgets.QGraphicsPixmapItem):
    def __init__(self, pixmap, speaker: SonosSpeaker):
        super().__init__()
        self.setPixmap(pixmap.scaled(80, 50, aspectRatioMode=QtCore.Qt.KeepAspectRatio))
        self.speaker = speaker

        self.title = QtWidgets.QGraphicsTextItem()
        self.title.setHtml(f'<div style="background:rgba(255, 255, 255, 75%)">{speaker.name}</div>')
        font: QtGui.QFont = self.title.font()
        font.setPointSizeF(18.0)
        self.title.setFont(font)
        self.title.setDefaultTextColor(QtGui.QColor(0, 0, 0))
        tc = self.title.boundingRect().width() / 2.0
        self.title.setParentItem(self)
        self.title.setPos(-tc, 50)

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        self.setCursor(QtCore.Qt.ClosedHandCursor)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        self.setCursor(QtCore.Qt.OpenHandCursor)

    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        if (
            QtCore.QLineF(event.screenPos(), event.buttonDownScreenPos(QtCore.Qt.LeftButton)).length()
            < QtWidgets.QApplication.startDragDistance()
        ):
            return

        drag = QtGui.QDrag(event.widget())
        mime = QtCore.QMimeData()
        mime.setData("text/sonos_ip", QtCore.QByteArray(self.speaker.ip_address.encode("utf-8")))
        drag.setMimeData(mime)

        drag.setPixmap(self.pixmap().scaled(40, 30))
        drag.setHotSpot(QtCore.QPoint(20, 15))

        drag.exec()


UNSET_GRADIENT = QtGui.QRadialGradient(0.55, 0.4, 0.65)
UNSET_GRADIENT.setCoordinateMode(QtGui.QGradient.ObjectMode)
UNSET_GRADIENT.setColorAt(0.0, QtGui.QColor(150, 50, 50))
UNSET_GRADIENT.setColorAt(1.0, QtGui.QColor(50, 0, 0))

SET_GRADIENT = QtGui.QRadialGradient(0.55, 0.4, 0.65)
SET_GRADIENT.setCoordinateMode(QtGui.QGradient.ObjectMode)
SET_GRADIENT.setColorAt(0.0, QtGui.QColor(50, 150, 50))
SET_GRADIENT.setColorAt(1.0, QtGui.QColor(0, 50, 0))


class SonosGroupGraphics(QtWidgets.QGraphicsEllipseItem):
    speakers: list[SonosSpeakerGraphics]

    def __init__(self, parent, group: SonosGroup, speaker_list: list[SonosSpeaker] = None):
        super().__init__(
            SonosGroupWidget.FULL_WIDGET_SCALE * 0.15,
            SonosGroupWidget.FULL_WIDGET_SCALE * 0.1,
            SonosGroupWidget.FULL_WIDGET_SCALE * 0.7,
            SonosGroupWidget.FULL_WIDGET_SCALE * 0.5,
        )
        self.group = group
        self.parent = parent

        self.setBrush(UNSET_GRADIENT)

        self.title = QtWidgets.QGraphicsTextItem(group.label)
        font: QtGui.QFont = self.title.font()
        font.setPointSizeF(20.0)
        font.setBold(True)
        self.title.setFont(font)
        self.title.setDefaultTextColor(QtGui.QColor(255, 255, 255))
        tc = self.title.boundingRect().width() / 2.0
        self.title.setParentItem(self)
        self.title.setPos(
            SonosGroupWidget.FULL_WIDGET_SCALE * 0.5 - tc, SonosGroupWidget.FULL_WIDGET_SCALE * 0.35 - 15.0
        )

        pixmap = QtGui.QPixmap()
        pixmap.load(os.path.join(BASE_PATH, "icons", "no_artwork.png"))

        if speaker_list is None:
            speaker_list = []
            for item in group.reference.members:
                if not item.is_visible:
                    continue
                si = item.get_speaker_info()
                speaker_list.append(SonosSpeaker(item.ip_address, si["model_name"], si["zone_name"], item))

        self.speakers = []
        for speaker in speaker_list:
            spkr_graph = SonosSpeakerGraphics(pixmap, speaker)
            self.speakers.append(spkr_graph)
        self.position_speakers()

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        self.parent.activate_group(self.group)

    def activate_group(self):
        self.setBrush(SET_GRADIENT)

    def deactivate_group(self):
        self.setBrush(UNSET_GRADIENT)

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
            spkr.setAcceptedMouseButtons(QtCore.Qt.LeftButton)
