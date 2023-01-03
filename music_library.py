"""
Build a copy of Artist/Album of the Sonos music library.

Download album art and store locally for quick access.
"""

import sqlite3
from PyQt5 import QtCore, QtGui

INSERT_QUERY = """INSERT INTO album_art
(artist, album, album_art, date) VALUES (?,?,?,?);"""

SEARCH_QUERY = """SELECT album_art,date FROM album_art
WHERE artist = ? AND album = ?;"""

def connect_db():
    global db
    db = sqlite3.connect('music_library.db')

def insert_image(artist, album, image, date):
    cursor = db.cursor()
    try:
        date = int(date)
    except ValueError:
        date = -1
    cursor.execute(INSERT_QUERY, (artist, album, image, date))
    db.commit()
    cursor.close()

def get_image(artist, album):
    cursor = db.cursor()
    cursor.execute(SEARCH_QUERY, (artist, album))
    rows = cursor.fetchall()
    cursor.close()

    if len(rows)>0:
        return tuple(rows[0])
    else:
        return None, 0

