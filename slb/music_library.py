"""
Build a copy of Artist/Album of the Sonos music library.

Download album art and store locally for quick access.
"""

import logging as log
import os
import sqlite3

INSERT_QUERY = """INSERT INTO album_art
(artist, album, album_art, date, genre) VALUES (?,?,?,?,?);"""

SEARCH_QUERY = """SELECT album_art,date FROM album_art
WHERE artist = ? AND album = ?;"""

SEARCH_QUERY_2 = """SELECT album_art,date FROM album_art
WHERE artist = ? ORDER BY date DESC;"""

GENRE_QUREY = """SELECT DISTINCT genre FROM album_art;"""
GENRE_COUNT_QUREY = """SELECT COUNT(album) FROM album_art WHERE genre = ?;"""
ALBUM_COUNT_QUREY= """SELECT COUNT(album) FROM album_art;"""

GENRE_ALBUMS_QUREY = """SELECT artist,album FROM album_art WHERE genre = ?;"""
ALBUM_ALL_QUREY= """SELECT artist,album FROM album_art;"""

ARTIST_QUREY = """SELECT DISTINCT artist FROM album_art ORDER BY artist ASC;"""
ARTIST_GENRE_QUREY = """SELECT DISTINCT artist, genre FROM album_art WHERE genre = ? ORDER BY artist ASC;"""


def connect_db():
    global db
    build_table = not os.path.exists("music_library.db")
    db = sqlite3.connect("music_library.db")

    if build_table:
        log.info("creating database")
        cursor = db.cursor()
        cursor.execute(
            """CREATE TABLE album_art (
                            id INTEGER PRIMARY KEY,
                            artist TEXT NOT NULL,
                            album TEXT NOT NULL,
                            album_art BLOB,
                            date INTEGER,
                            genre TEXT);"""
        )
        cursor.close()
        db.commit()


def insert_image(artist, album, image, date, genre=None):
    cursor = db.cursor()
    try:
        date = int(date)
    except ValueError:
        date = -1
    cursor.execute(INSERT_QUERY, (artist, album, image, date, genre))
    db.commit()
    cursor.close()


def get_image(artist, album):
    cursor = db.cursor()
    cursor.execute(SEARCH_QUERY, (artist, album))
    rows = cursor.fetchall()
    cursor.close()

    if len(rows) > 0:
        return tuple(rows[0])
    else:
        return None, 0


def get_last_image(artist):
    cursor = db.cursor()
    cursor.execute(SEARCH_QUERY_2, (artist,))
    rows = cursor.fetchall()
    cursor.close()

    if len(rows) > 0:
        return tuple(rows[0])
    else:
        return None, 0


def get_genre_list():
    cursor = db.cursor()
    cursor.execute(GENRE_QUREY)
    rows = cursor.fetchall()
    cursor.close()
    return [line[0] for line in rows if line[0] is not None]

def get_num_albums(genre=None):
    cursor = db.cursor()
    if genre is None:
        cursor.execute(ALBUM_COUNT_QUREY)
    else:
        cursor.execute(GENRE_COUNT_QUREY, (genre,))
    rows = cursor.fetchall()
    cursor.close()
    return int(rows[0][0])

def get_albums(genre=None):
    cursor = db.cursor()
    if genre is None:
        cursor.execute(ALBUM_ALL_QUREY)
    else:
        cursor.execute(GENRE_ALBUMS_QUREY, (genre,))
    rows = cursor.fetchall()
    cursor.close()
    return list(rows)


def get_artists(genre=None):
    cursor = db.cursor()
    if genre is None:
        cursor.execute(ARTIST_QUREY)
    else:
        cursor.execute(ARTIST_GENRE_QUREY, (genre,))
    rows = cursor.fetchall()
    cursor.close()
    return [line[0] for line in rows if line[0] is not None]
