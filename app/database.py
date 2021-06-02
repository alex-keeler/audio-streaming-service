import mysql.connector
from app.util import calculate_time

class Database(object):
    def __init__(self, username_str, password_str, db_name_str, host_str='localhost'):
        """
        Creates a new MySQL database with the given username, password, database name, and host
        (optional).
        username_str: The username used to access the database (str)
        password_str: The password used to access the database (str)
        db_name_str: The name of the database being accessed (str)
        host_str: The IP of the host (defaults to localhost if left empty) (str)
        """

        self.username = username_str
        self.password = password_str
        self.db_name = db_name_str
        self.host = host_str

    def open_connection(self):
        """
        Opens a new connection to the database and returns the connection and a cursor used to
        navigate the database.
        Returns: A connection to the database (mysql.connector), a cursor (mysql.connector.cursor)
        Note: Remember to close the cursor and database connection when you are done with them!
        """

        cnx = mysql.connector.connect(username=self.username, password=self.password,
            database=self.db_name, host=self.host)

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
                    " JOIN artist ar ON al.artist_id = ar.id ")

        cursor.execute(query)

        results = []

        for result in cursor:
            result_list = list(result)
            result_list[2] = calculate_time(result_list[2])
            results.append(tuple(result_list))

        cursor.close()
        cnx.close()

        return tuple(results)

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


    def get_album_by_id(self, album_id):
        # 0=id, 1=name, 2=year_released, 3=artist_id

        cnx, cursor = self.open_connection()

        query = (" SELECT a.* FROM album a " +
                    " WHERE a.id = {}").format(album_id)

        cursor.exeute(query)

        results = []

        for result in cursor:
            results.append(result)

        cursor.close()
        cnx.close()

        return self.get_first_or_none(results)

    def get_album_by_name_and_artist_id(self, album_name, artist_id):
        # 0=id, 1=name

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