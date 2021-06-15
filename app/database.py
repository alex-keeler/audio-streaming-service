import mysql.connector
from app import app
from app.util import calculate_time
import random
import os
import boto3

ENDPOINT="rds-endpoint"
PORT="3306"
DBNAME="audiostream"
USR="audiouser"
PASSWORD="audiouser"
REGION="us-east-1"
SSL_CA = "/path/to/secret.pem"
os.environ['LIBMYSQL_ENABLE_CLEARTEXT_PLUGIN'] = '1'

class Database(object):
    def __init__(self, rds=False, host="localhost", user="audiouser", password="audiouser", port=3306, database="audiostream", ssl_ca=None):

        self.rds = rds
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.database = database
        self.ssl_ca = ssl_ca

    def open_connection(self):
        """
        Opens a new connection to the database and returns the connection and a cursor used to
        navigate the database.
        Returns: A connection to the database (mysql.connector), a cursor (mysql.connector.cursor)
        Note: Remember to close the cursor and database connection when you are done with them!
        """

        cnx = mysql.connector.connect(username=self.user, password=self.password,
            database=self.database, host=self.host)

        return cnx, cnx.cursor()

    def get_song_by_id(self, song_id):
        # 0=id, 1=name, 2=length, 3=track_number, 4=album_id, 5=file_uuid

        cnx, cursor = self.open_connection()

        query = (" SELECT s.* FROM song s " +
                    " WHERE s.id = {}").format(song_id)

        cursor.execute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return self.get_first_or_none(results)


    def get_song_by_id_loaded(self, song_id):
        # 0=id, 1=name, 2=length, 3=track_number, 4=album_id, 5=file_uuid, 6=album_name, 7=artist_name

        cnx, cursor = self.open_connection()

        query = (" SELECT s.*, al.name, ar.name FROM song s " +
                    " JOIN album al ON s.album_id = al.id " +
                    " JOIN artist ar ON al.artist_id = ar.id " +
                    " WHERE s.id = {} ").format(song_id)

        cursor.execute(query)

        results = []

        for result in cursor:
            result_list = list(result)
            result_list[2] = calculate_time(result_list[2]) # length
            results.append(tuple(result_list))

        cursor.close()
        cnx.close()

        return self.get_first_or_none(results)

    def get_all_songs(self):
        # 0=id, 1=name, 2=length, 3=track_number, 4=album_id, 5=file_uuid

        cnx, cursor = self.open_connection()

        query = (" SELECT s.* FROM song s ")

        cursor.execute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return tuple(results)

    def get_all_songs_loaded(self):
        # 0=id, 1=name, 2=length, 3=track_number, 4=album_id, 5=file_uuid, 6=album_name, 7=artist_name

        cnx, cursor = self.open_connection()

        query = (" SELECT s.*, al.name, ar.name FROM song s " +
                    " JOIN album al ON s.album_id = al.id " +
                    " JOIN artist ar ON al.artist_id = ar.id " +
                    " ORDER BY ar.name, al.name, s.track_number, s.id ")

        cursor.execute(query)

        results = []

        for result in cursor:
            result_list = list(result)
            result_list[2] = calculate_time(result_list[2]) # length
            results.append(tuple(result_list))

        cursor.close()
        cnx.close()

        return tuple(results)

    def get_songs_by_album_id(self, album_id):
        # 0=id, 1=name, 2=length, 3=track_number, 4=album_id, 5=file_uuid

        cnx, cursor = self.open_connection()

        query = (" SELECT s.* FROM song s " +
                    " WHERE s.album_id = {} ").format(album_id)

        cursor.execute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return results

    def get_songs_by_album_id_loaded(self, album_id):
        # 0=id, 1=name, 2=length, 3=track_number, 4=album_id, 5=file_uuid, 6=album_name, 7=artist_name

        cnx, cursor = self.open_connection()

        query = (" SELECT s.*, al.name, ar.name FROM song s " +
                    " JOIN album al ON s.album_id = al.id " +
                    " JOIN artist ar ON al.artist_id = ar.id " +
                    " WHERE al.id = {} " +
                    " ORDER BY ar.name, al.name, s.track_number, s.id ").format(
                        album_id)

        cursor.execute(query)

        results = []

        for result in cursor:
            result_list = list(result)
            result_list[2] = calculate_time(result_list[2]) # length
            results.append(tuple(result_list))

        cursor.close()
        cnx.close()

        return results

    def get_songs_by_artist_id_loaded(self, artist_id):
        # 0=id, 1=name, 2=length, 3=track_number, 4=album_id, 5=file_uuid, 6=album_name, 7=artist_name

        cnx, cursor = self.open_connection()

        query = (" SELECT s.*, al.name, ar.name FROM song s " +
                    " JOIN album al ON s.album_id = al.id " +
                    " JOIN artist ar ON al.artist_id = ar.id " +
                    " WHERE ar.id = {} " +
                    " ORDER BY ar.name, al.name, s.track_number, s.id ").format(
                        artist_id)

        cursor.execute(query)

        results = []

        for result in cursor:
            result_list = list(result)
            result_list[2] = calculate_time(result_list[2]) # length
            results.append(tuple(result_list))

        cursor.close()
        cnx.close()

        return results

    def save_song(self, song_name, song_length, track_number, album_name, album_release_year, artist_name):

        artist = self.get_artist_by_name(artist_name)
        artist_id = artist[0] if artist else self.save_artist(artist_name)

        album = self.get_album_by_name_and_artist_id(album_name, artist_id)
        album_id = album[0] if album else self.save_album(album_name, album_release_year, artist_id)

        cnx, cursor = self.open_connection()

        query = (" INSERT INTO song (name, length, track_number, album_id, file_uuid) " +
                    " VALUES (\"{}\", {}, {}, {}, uuid()) ").format(song_name, self.nullable(song_length), self.nullable(track_number), album_id)

        cursor.execute(query)

        created_id = cursor.lastrowid

        cnx.commit()
        cursor.close()
        cnx.close()

        return created_id

    def delete_song(self, song_id):

        cnx, cursor = self.open_connection()

        album_id = self.get_song_by_id(song_id)[4]

        query = (" DELETE FROM song " +
                    " WHERE id = {} ").format(song_id)

        cursor.execute(query)

        cnx.commit()
        cursor.close()
        cnx.close()

        if len(self.get_songs_by_album_id(album_id)) == 0:
            self.delete_album(album_id)

    def get_album_by_id(self, album_id):
        # 0=id, 1=name, 2=year_released, 3=artist_id, 4=cover_file_uuid

        cnx, cursor = self.open_connection()

        query = (" SELECT a.* FROM album a " +
                    " WHERE a.id = {}").format(album_id)

        cursor.execute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return self.get_first_or_none(results)

    def get_album_by_name_and_artist_id(self, album_name, artist_id):
        # 0=id, 1=name, 2=year_released, 3=artist_id, 4=cover_file_uuid

        cnx, cursor = self.open_connection()

        query = (" SELECT a.* FROM album a " +
                    " WHERE a.name = \"{}\" AND artist_id = {}").format(
                        album_name, artist_id)

        cursor.execute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return self.get_first_or_none(results)

    def get_all_albums(self):
        # 0=id, 1=name, 2=year_released, 3=artist_id, 4=cover_file_uuid

        cnx, cursor = self.open_connection()

        query = (" SELECT a.* FROM album a ")

        cursor.execute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return tuple(results)

    def get_all_albums_loaded(self):
        # 0=id, 1=name, 2=year_released, 3=artist_id, 4=cover_file_uuid, 5=artist_name

        cnx, cursor = self.open_connection()

        query = (" SELECT al.*, ar.name FROM album al " +
                    " JOIN artist ar ON ar.id = al.artist_id " +
                    " ORDER BY ar.name, al.name ")

        cursor.execute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return tuple(results)

    @app.route("/get_artist_by_id")
    def get_artist_by_id(self, artist_id):
        # 0=id, 1=name

        cnx, cursor = self.open_connection()

        query = (" SELECT a.* FROM artist a " +
                    " WHERE a.id = {}").format(artist_id)

        cursor.execute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return self.get_first_or_none(results)

    def get_all_artists(self):
        # 0=id, 1=artist_name

        cnx, cursor = self.open_connection()

        query = (" SELECT a.* FROM artist a " +
                    " ORDER BY a.name ")

        cursor.execute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return tuple(results)

    def get_albums_by_artist_id(self, artist_id):
        # 0=id, 1=name, 2=year_released, 3=artist_id, 4=cover_file_uuid

        cnx, cursor = self.open_connection()

        query = (" SELECT a.* FROM album a " +
                    " WHERE a.artist_id = {} ").format(artist_id)
        cursor.execute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return results

    def get_albums_by_artist_id_loaded(self, artist_id):
        # 0=id, 1=name, 2=year_released, 3=artist_id, 4=cover_file_uuid, 5=artist_name

        cnx, cursor = self.open_connection()

        query = (" SELECT al.*, ar.name FROM album al " +
                    " JOIN artist ar ON ar.id = al.artist_id "
                    " WHERE al.artist_id = {} " +
                    " ORDER BY ar.name, al.name ").format(artist_id)
        cursor.execute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return results

    def save_album(self, album_name, year_released, artist_id):

        cnx, cursor = self.open_connection()

        query = (" INSERT INTO album (name, year_released, artist_id) " +
                    " VALUES (\"{}\", {}, {}) ").format(
                        album_name, self.nullable(year_released), artist_id)

        cursor.execute(query)

        created_id = cursor.lastrowid

        cnx.commit()
        cursor.close()
        cnx.close()

        return created_id

    def delete_album(self, album_id):

        cnx, cursor = self.open_connection()

        artist_id = self.get_album_by_id(album_id)[3]

        query = (" DELETE FROM album " +
                    " WHERE id = {} ").format(album_id)

        cursor.execute(query)

        cnx.commit()
        cursor.close()
        cnx.close()

        if len(self.get_albums_by_artist_id(artist_id)) == 0:
            self.delete_artist(artist_id)

    def get_artist_by_name(self, artist_name):
        # 0=id, 1=name

        cnx, cursor = self.open_connection()

        query = (" SELECT a.* FROM artist a " +
                    " WHERE a.name = \"{}\"").format(artist_name)

        cursor.execute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return self.get_first_or_none(results)

    def save_artist(self, artist_name):

        cnx, cursor = self.open_connection()

        query = (" INSERT INTO artist (name) " +
                    " VALUES (\"{}\") ").format(artist_name)

        cursor.execute(query)

        created_id = cursor.lastrowid

        cnx.commit()
        cursor.close()
        cnx.close()

        return created_id

    def delete_artist(self, artist_id):

        cnx, cursor = self.open_connection()

        query = (" DELETE FROM artist " +
                    " WHERE id = {} ").format(artist_id)

        cursor.execute(query)

        cnx.commit()
        cursor.close()
        cnx.close()

    def get_all_playlists(self):
        # 0=id, 1=name, 2=description, 3=date_created

        cnx, cursor = self.open_connection()

        query = (" SELECT p.* FROM playlist p " +
                    " ORDER BY p.date_created ")

        cursor.execute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return results


    def get_playlist_by_id(self, playlist_id):
        # 0=id, 1=name, 2=description, 3=date_created

        cnx, cursor = self.open_connection()

        query = (" SELECT p.* FROM playlist p " +
                    " WHERE p.id = {} ".format(playlist_id))

        cursor.execute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return self.get_first_or_none(results)

    def get_playlist_by_name(self, playlist_name):
        # 0=id, 1=name, 2=description, 3=date_created

        cnx, cursor = self.open_connection()

        query = (" SELECT p.* FROM playlist p " +
                    " WHERE p.name = \"{}\" ".format(playlist_name))

        cursor.execute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return self.get_first_or_none(results)

    def get_playlist_songs_by_playlist_id_loaded(self, playlist_id):
        # playlist_song (ps):   0=ps.id, 1=ps.date_added, 2=ps.previous_playlist_song_id, 3=ps.next_playlist_song_id,
        #                       4=ps.playlist_group, 5=ps.order, 6=ps.playlist_id, 7=ps.song_id,
        # song (s):             8=s.name, 9=s.length, 10=s.file_uuid,
        # album (al):           11=al.name,
        # artist (ar):          12=ar.name

        cnx, cursor = self.open_connection()

        query = (" SELECT ps.*, s.name, s.length, s.file_uuid, al.name, ar.name FROM playlist_song ps " +
                    " JOIN playlist p ON p.id = ps.playlist_id " +
                    " JOIN song s ON s.id = ps.song_id " +
                    " JOIN album al ON al.id = s.album_id " +
                    " JOIN artist ar ON ar.id = al.artist_id " +
                    " WHERE p.id = {} " +
                    " ORDER BY ps.order, ps.id ").format(playlist_id)

        cursor.execute(query)

        results = []

        for query_result in cursor:
            result_list = list(query_result)
            result_list[9] = calculate_time(result_list[9]) # length
            results.append(tuple(result_list))

        cursor.close()
        cnx.close()

        return results

    def get_songs_by_playlist_id_loaded(self, playlist_id):
        # song(s):              0=s.id, 1=s.name, 2=s.length, 3=s.track_number, 4=s.album_id, 5=s.file_uuid, 6=s.album_name, 7=s.artist_name
        # playlist_song (ps):   8=ps.id, 9=ps.date_added, 10=ps.previous_playlist_song_id, 11=ps.next_playlist_song_id,
        #                       12=ps.playlist_group, 13=ps.order, 14=ps.playlist_id, 15=ps.song_id

        cnx, cursor = self.open_connection()

        query = (" SELECT s.*, al.name, ar.name, ps.* FROM playlist_song ps " +
                    " JOIN playlist p ON p.id = ps.playlist_id " +
                    " JOIN song s ON s.id = ps.song_id " +
                    " JOIN album al ON al.id = s.album_id " +
                    " JOIN artist ar ON ar.id = al.artist_id " +
                    " WHERE p.id = {} ".format(playlist_id))

        cursor.execute(query)

        results = []

        for query_result in cursor:
            result_list = list(query_result)
            result_list[2] = calculate_time(result_list[2]) # length
            results.append(tuple(result_list))

        cursor.close()
        cnx.close()

        return results

    def get_playlist_song_by_id(self, playlist_song_id):
        # 0=id, 1=date_added, 2=previous_playlist_song_id, 3=next_playlist_song_id, 4=playlist_group, 5=order, 6=playlist_id, 7=song_id

        cnx, cursor = self.open_connection()

        query = (" SELECT ps.* FROM playlist_song ps " +
                    " WHERE ps.id = {} ").format(
                        playlist_song_id)

        cursor.execute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return self.get_first_or_none(results)

    def get_playlist_song_by_playlist_and_song(self, playlist_id, song_id):
        # 0=id, 1=date_added, 2=previous_playlist_song_id, 3=next_playlist_song_id, 4=playlist_group, 5=order, 6=playlist_id, 7=song_id

        cnx, cursor = self.open_connection()

        query = (" SELECT ps.* FROM playlist_song ps " +
                    " WHERE ps.playlist_id = {} AND ps.song_id = {} ").format(
                        playlist_id, song_id)

        cursor.execute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return self.get_first_or_none(results)

    def generate_playlist_queue(self, playlist_id, shuffle=False, group_songs=False):
        # song(s):              0=s.id, 1=s.name, 2=s.length, 3=s.track_number, 4=s.album_id, 5=s.file_uuid, 6=s.album_name, 7=s.artist_name
        # playlist_song (ps):   8=ps.id, 9=ps.date_added, 10=ps.previous_playlist_song_id, 11=ps.next_playlist_song_id,
        #                       12=ps.playlist_group, 13=ps.order, 14=ps.playlist_id, 15=ps.song_id

        songs = self.get_songs_by_playlist_id_loaded(playlist_id)

        if shuffle:
            random.shuffle(songs)

        if group_songs:
            songs_out = []
            song_dict = {}

            # populate song lookup dictionary
            for song in songs:
                song_dict[song[8]] = song # key = id, value = object

            # populate songs_out
            for song in songs:
                # if there is a previous song in the group, skip
                if song[10] is None:
                    songs_out.append(song)

                    # queue up entire group once we find the head
                    if song[11] is not None:
                        next_playlist_song_id = song[11]
                        while next_playlist_song_id is not None:
                            group_song = song_dict[next_playlist_song_id]
                            songs_out.append(group_song)
                            next_playlist_song_id = group_song[11]

        else:
            songs_out = songs

        return songs_out

    def save_playlist(self, name, description):

        cnx, cursor = self.open_connection()

        query = (" INSERT INTO playlist (name, description, date_created) " +
                    " VALUES (\"{}\", \"{}\", now()) ".format(name, self.nullable(description)))

        cursor.execute(query)

        created_id = cursor.lastrowid

        cnx.commit()
        cursor.close()
        cnx.close()

        return created_id

    def save_playlist_song(self, playlist_id, song_id, previous_playlist_song_id, playlist_group):

        cnx, cursor = self.open_connection()

        query = (" INSERT INTO playlist_song (playlist_id, song_id, date_added, " +
                    " previous_playlist_song_id, playlist_group) " +
                    " VALUES ({}, {}, now(), {}, {}) ".format(playlist_id, song_id,
                        self.nullable(previous_playlist_song_id), self.nullable(playlist_group)))

        cursor.execute(query)

        created_id = cursor.lastrowid

        cnx.commit()
        cursor.close()
        cnx.close()

        return created_id

    def delete_playlist_song(self, playlist_song_id):

        cnx, cursor = self.open_connection()

        query = (" DELETE FROM playlist_song " +
                    " WHERE id = {} ").format(playlist_song_id)

        cursor.execute(query)

        cnx.commit()
        cursor.close()
        cnx.close()

    def delete_playlist(self, playlist_id):

        cnx, cursor = self.open_connection()

        query = (" DELETE FROM playlist_song " +
                    " WHERE playlist_id = {} ").format(playlist_id)

        cursor.execute(query)

        query = (" DELETE FROM playlist " +
                    " WHERE id = {} ").format(playlist_id)

        cursor.execute(query)

        cnx.commit()
        cursor.close()
        cnx.close()

    @staticmethod
    def nullable(value):
        return value if value is not None else "NULL"

    @staticmethod
    def sanitize(in_str):
        """
        Sanitizes and returns any string input used in an SQL Query to prevent SQL Injection
        in_str: The string to be sanitized (str)
        Returns: The sanitized string (str)
        """

        out_str = ""

        for char in in_str:
            if char == "'" or char == '"':
                out_str += "\\" + char
            else:
                out_str += char

        return out_str

    @staticmethod
    def get_first_or_none(results):

        if len(results) == 0:
            return None
        else:
            return tuple(results[0])

# session = boto3.Session(profile_name='default')
# client = session.client('rds')

# token = client.generate_db_auth_token(DBHostname=ENDPOINT, Port=PORT, DBUsername=USR, Region=REGION)

# Uncomment for RDS database:
# db = Database(rds=True, host=ENDPOINT, user=USR, password=PASSWORD, port=PORT, database=DBNAME, ssl_ca=SSL_CA)

# Local database
db = Database()
