from PyQt5 import QtWidgets, QtGui

class AlbumArtworkLabel(QtWidgets.QLabel):
    def setPixmap(self, pixmap):
        super().setPixmap(pixmap)
        self.updateMargins()

    def resizeEvent(self, *args, **kwargs):
        self.updateMargins()
        super().resizeEvent(*args, **kwargs)

    def updateMargins(self):
        img_ratio = self.pixmap().width()/max(1, self.pixmap().height())
        w = self.width()
        h = self.height()*img_ratio

        if w>h:
            m = int((w-h)/2)
            self.setContentsMargins(m, 0, m, 0)
        elif h>w:
            m = int((h-w)/2)
            self.setContentsMargins(0, m, 0, m)

class LibraryView(QtWidgets.QGraphicsView):
    FULL_LIBRARY_WIDTH = 1500

    def resizeEvent(self, QResizeEvent):
        w = self.width()-self.verticalScrollBar().width()
        s = w/self.FULL_LIBRARY_WIDTH
        T = QtGui.QTransform(s, 0., 0., s, 0., 0.)
        self.setTransform(T)