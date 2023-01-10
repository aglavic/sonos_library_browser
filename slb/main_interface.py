# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\main_interface.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(820, 518)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.libraryView = LibraryView(self.centralwidget)
        self.libraryView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.libraryView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.libraryView.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        self.libraryView.setObjectName("libraryView")
        self.verticalLayout_3.addWidget(self.libraryView)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 820, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.toolBar = QtWidgets.QToolBar(MainWindow)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.BottomToolBarArea, self.toolBar)
        self.groupsDock = QtWidgets.QDockWidget(MainWindow)
        self.groupsDock.setObjectName("groupsDock")
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_6.setContentsMargins(4, 4, 4, 4)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.groupList = QtWidgets.QListWidget(self.dockWidgetContents)
        self.groupList.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.groupList.setObjectName("groupList")
        self.verticalLayout_6.addWidget(self.groupList)
        self.label_7 = QtWidgets.QLabel(self.dockWidgetContents)
        self.label_7.setObjectName("label_7")
        self.verticalLayout_6.addWidget(self.label_7)
        self.speakerList = QtWidgets.QListWidget(self.dockWidgetContents)
        self.speakerList.setObjectName("speakerList")
        self.verticalLayout_6.addWidget(self.speakerList)
        self.groupsDock.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.groupsDock)
        self.queueDock = QtWidgets.QDockWidget(MainWindow)
        self.queueDock.setObjectName("queueDock")
        self.dockWidgetContents_2 = QtWidgets.QWidget()
        self.dockWidgetContents_2.setObjectName("dockWidgetContents_2")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.dockWidgetContents_2)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupQueueList = QtWidgets.QListWidget(self.dockWidgetContents_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupQueueList.sizePolicy().hasHeightForWidth())
        self.groupQueueList.setSizePolicy(sizePolicy)
        self.groupQueueList.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.groupQueueList.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.groupQueueList.setObjectName("groupQueueList")
        self.verticalLayout.addWidget(self.groupQueueList)
        self.queueDock.setWidget(self.dockWidgetContents_2)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.queueDock)
        self.settingsDock = QtWidgets.QDockWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.settingsDock.sizePolicy().hasHeightForWidth())
        self.settingsDock.setSizePolicy(sizePolicy)
        self.settingsDock.setObjectName("settingsDock")
        self.dockWidgetContents_3 = QtWidgets.QWidget()
        self.dockWidgetContents_3.setObjectName("dockWidgetContents_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.dockWidgetContents_3)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.iconSizeBox = QtWidgets.QComboBox(self.dockWidgetContents_3)
        self.iconSizeBox.setObjectName("iconSizeBox")
        self.iconSizeBox.addItem("")
        self.iconSizeBox.addItem("")
        self.iconSizeBox.addItem("")
        self.verticalLayout_2.addWidget(self.iconSizeBox)
        self.artistFilter = QtWidgets.QLineEdit(self.dockWidgetContents_3)
        self.artistFilter.setObjectName("artistFilter")
        self.verticalLayout_2.addWidget(self.artistFilter)
        self.settingsDock.setWidget(self.dockWidgetContents_3)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.settingsDock)
        self.nowPlayingDock = QtWidgets.QDockWidget(MainWindow)
        self.nowPlayingDock.setObjectName("nowPlayingDock")
        self.dockWidgetContents_5 = QtWidgets.QWidget()
        self.dockWidgetContents_5.setObjectName("dockWidgetContents_5")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.dockWidgetContents_5)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.NowPlayingGroup = QtWidgets.QLabel(self.dockWidgetContents_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.NowPlayingGroup.sizePolicy().hasHeightForWidth())
        self.NowPlayingGroup.setSizePolicy(sizePolicy)
        self.NowPlayingGroup.setObjectName("NowPlayingGroup")
        self.verticalLayout_4.addWidget(self.NowPlayingGroup)
        self.NowPlayingArt = AlbumArtworkLabel(self.dockWidgetContents_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.NowPlayingArt.sizePolicy().hasHeightForWidth())
        self.NowPlayingArt.setSizePolicy(sizePolicy)
        self.NowPlayingArt.setScaledContents(True)
        self.NowPlayingArt.setObjectName("NowPlayingArt")
        self.verticalLayout_4.addWidget(self.NowPlayingArt)
        self.NowPlayingArtist = QtWidgets.QLabel(self.dockWidgetContents_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.NowPlayingArtist.sizePolicy().hasHeightForWidth())
        self.NowPlayingArtist.setSizePolicy(sizePolicy)
        self.NowPlayingArtist.setObjectName("NowPlayingArtist")
        self.verticalLayout_4.addWidget(self.NowPlayingArtist)
        self.NowPlayingAlbum = QtWidgets.QLabel(self.dockWidgetContents_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.NowPlayingAlbum.sizePolicy().hasHeightForWidth())
        self.NowPlayingAlbum.setSizePolicy(sizePolicy)
        self.NowPlayingAlbum.setObjectName("NowPlayingAlbum")
        self.verticalLayout_4.addWidget(self.NowPlayingAlbum)
        self.NowPlayingTrack = QtWidgets.QLabel(self.dockWidgetContents_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.NowPlayingTrack.sizePolicy().hasHeightForWidth())
        self.NowPlayingTrack.setSizePolicy(sizePolicy)
        self.NowPlayingTrack.setObjectName("NowPlayingTrack")
        self.verticalLayout_4.addWidget(self.NowPlayingTrack)
        self.NowPlayingTime = QtWidgets.QLabel(self.dockWidgetContents_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.NowPlayingTime.sizePolicy().hasHeightForWidth())
        self.NowPlayingTime.setSizePolicy(sizePolicy)
        self.NowPlayingTime.setObjectName("NowPlayingTime")
        self.verticalLayout_4.addWidget(self.NowPlayingTime)
        self.nowPlayingDock.setWidget(self.dockWidgetContents_5)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.nowPlayingDock)
        self.actionBack = QtWidgets.QAction(MainWindow)
        self.actionBack.setObjectName("actionBack")
        self.actionPlay_Pause = QtWidgets.QAction(MainWindow)
        self.actionPlay_Pause.setObjectName("actionPlay_Pause")
        self.actionForward = QtWidgets.QAction(MainWindow)
        self.actionForward.setObjectName("actionForward")
        self.actionStop = QtWidgets.QAction(MainWindow)
        self.actionStop.setObjectName("actionStop")
        self.nowPlayingDock.raise_()
        self.toolBar.addAction(self.actionBack)
        self.toolBar.addAction(self.actionPlay_Pause)
        self.toolBar.addAction(self.actionStop)
        self.toolBar.addAction(self.actionForward)

        self.retranslateUi(MainWindow)
        self.groupList.currentRowChanged["int"].connect(MainWindow.update_playing)  # type: ignore
        self.actionBack.triggered.connect(MainWindow.queue_prev)  # type: ignore
        self.actionPlay_Pause.triggered.connect(MainWindow.queue_play_pause)  # type: ignore
        self.actionStop.triggered.connect(MainWindow.queue_stop)  # type: ignore
        self.actionForward.triggered.connect(MainWindow.queue_next)  # type: ignore
        self.iconSizeBox.currentIndexChanged["int"].connect(MainWindow.change_icon_size)  # type: ignore
        self.artistFilter.textEdited["QString"].connect(MainWindow.filter_artists)  # type: ignore
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Sonos Library Browser"))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.groupsDock.setWindowTitle(_translate("MainWindow", "Groups"))
        self.label_7.setText(_translate("MainWindow", "Speakers"))
        self.queueDock.setWindowTitle(_translate("MainWindow", "Group Queue"))
        self.settingsDock.setWindowTitle(_translate("MainWindow", "Settings"))
        self.iconSizeBox.setItemText(0, _translate("MainWindow", "small"))
        self.iconSizeBox.setItemText(1, _translate("MainWindow", "medium"))
        self.iconSizeBox.setItemText(2, _translate("MainWindow", "large"))
        self.artistFilter.setPlaceholderText(_translate("MainWindow", "filter artists"))
        self.nowPlayingDock.setWindowTitle(_translate("MainWindow", "Playing..."))
        self.NowPlayingGroup.setToolTip(_translate("MainWindow", "Active Groupe"))
        self.NowPlayingGroup.setText(_translate("MainWindow", "{?}"))
        self.NowPlayingArt.setText(_translate("MainWindow", "Image"))
        self.NowPlayingArtist.setToolTip(_translate("MainWindow", "Artist"))
        self.NowPlayingArtist.setText(_translate("MainWindow", "{?}"))
        self.NowPlayingAlbum.setToolTip(_translate("MainWindow", "Album"))
        self.NowPlayingAlbum.setText(_translate("MainWindow", "{?}"))
        self.NowPlayingTrack.setToolTip(_translate("MainWindow", "Track"))
        self.NowPlayingTrack.setText(_translate("MainWindow", "{?}"))
        self.NowPlayingTime.setToolTip(_translate("MainWindow", "Time"))
        self.NowPlayingTime.setText(_translate("MainWindow", "{?}"))
        self.actionBack.setText(_translate("MainWindow", "Back"))
        self.actionPlay_Pause.setText(_translate("MainWindow", "Play/Pause"))
        self.actionForward.setText(_translate("MainWindow", "Forward"))
        self.actionStop.setText(_translate("MainWindow", "Stop"))


from simple_widgets import AlbumArtworkLabel, LibraryView