from app import app
from flask import Flask, render_template, redirect, url_for, flash, session, Response, request
import PyWave
from app.s3storage import create_presigned_url, upload_file, delete_file, BUCKET_NAME
from app.database import db
from app.forms import UploadSongForm, AddSongToPlaylistForm, CreatePlaylistForm
from werkzeug.utils import secure_filename
from mutagen.mp3 import MP3
import os
import json

SAMPLES = 65536
RATE = 44100
BITS_PER_SAMPLE = 16
CHANNELS = 2
LENGTH = 15

@app.route("/")
@app.route("/index")
@app.route("/home")
def index():
	return render_template("home.html")

@app.route("/playlists")
def playlists():
	playlists = db.get_all_playlists()

	return render_template("playlists.html", playlists=playlists)

@app.route("/playlist")
def playlist():
	playlist_id = request.args.get('playlist_id')

	playlist = db.get_playlist_by_id(playlist_id)
	playlist_songs = db.get_playlist_songs_by_playlist_id_loaded(playlist_id)

	return render_template("playlist.html", playlist=playlist, songs=playlist_songs)

@app.route("/playlist/create", methods=['get', 'post'])
def create_playlist():
	form = CreatePlaylistForm()

	if form.validate_on_submit():
		playlist_name = form.playlist_name.data
		duplicate = db.get_playlist_by_name(playlist_name)
		if duplicate is None:
			db.save_playlist(playlist_name, None)
			flash("Playlist created!")
			return redirect(url_for("playlists"))
		else:
			flash("A playlist with that name already exists!")

	return render_template("create_playlist.html", form=form)

@app.route("/artists")
def artists():
	artists = db.get_all_artists()

	return render_template("artists.html", artists=artists)

@app.route("/albums")
def albums():
	artist_id = request.args.get('artist_id')
	artist_name = db.get_artist_by_id(artist_id)[1] if artist_id is not None else None

	if artist_id is not None:
		albums = db.get_albums_by_artist_id_loaded(artist_id)
	else:
		albums = db.get_all_albums_loaded()

	return render_template("albums.html", albums=albums, artist_name=artist_name)

@app.route("/songs")
def songs():
	album_id = request.args.get('album_id')
	album_name = db.get_album_by_id(album_id)[1] if album_id is not None else None

	artist_id = request.args.get('artist_id')
	artist_name = db.get_artist_by_id(artist_id)[1] if artist_id is not None else None

	if album_id is not None:
		songs = db.get_songs_by_album_id_loaded(album_id)
	elif artist_id is not None:
		songs = db.get_songs_by_artist_id_loaded(artist_id)
	else:
		songs = db.get_all_songs_loaded()

	return render_template("songs.html", songs=songs, album_id=album_id, album_name=album_name, artist_id=artist_id, artist_name=artist_name)

@app.route("/delete-song")
def delete_song():
	song_id = request.args.get('song_id')

	# only used for redirect back to songs page
	album_id = request.args.get('album_id')
	artist_id = request.args.get('artist_id')

	song_file_uuid = db.get_song_by_id(song_id)[5]

	db.delete_song(song_id)
	delete_file(BUCKET_NAME, song_file_uuid + ".mp3")
	flash("Song successfully deleted!")

	return redirect(url_for("songs", album_id=album_id, artist_id=artist_id))

# DEPRECATED
@app.route("/upload-song")
def upload_song():
	song_form = UploadSongForm()

	return render_template("file_upload_to_s3.html", form=song_form)

@app.route("/add-song-to-playlist", methods=['get', 'post'])
def add_song_to_playlist():
	song_id = request.args.get('song_id')
	song = db.get_song_by_id_loaded(song_id)
	form = AddSongToPlaylistForm(song_id=song_id)
	form.playlist_id.choices = [(playlist[0], playlist[1]) for playlist in db.get_all_playlists()]

	if form.validate_on_submit():
		song_id = form.song_id.data
		playlist_id = form.playlist_id.data
		duplicate = db.get_playlist_song_by_playlist_and_song(playlist_id, song_id)
		if duplicate is None:
			db.save_playlist_song(playlist_id, song_id, None, None)
			flash("Song successfully added to playlist!")
			return redirect(url_for("songs"))
		else:
			flash("Song is already in playlist!")

	return render_template("add_song_to_playlist.html", form=form, song=song)

@app.route("/remove-song-from-playlist")
def delete_playlist_song():
	playlist_song_id = request.args.get('playlist_song_id')

	playlist_id = db.get_playlist_song_by_id(playlist_song_id)[6]

	db.delete_playlist_song(playlist_song_id)
	flash("Song removed from playlist!")

	return redirect(url_for("playlist", playlist_id=playlist_id))

@app.route("/delete-playlist")
def delete_playlist():
	playlist_id = request.args.get('playlist_id')

	db.delete_playlist(playlist_id)
	flash("Playlist deleted!")

	return redirect(url_for("playlists"))


@app.route('/upload', methods=['get', 'post'])
def upload():

	form = UploadSongForm()

	if form.validate_on_submit():
		song_file = request.files[form.song_file.name]
		song_filename = secure_filename(song_file.filename)
		song_file.save(song_filename)

		audio = MP3(song_file)
		song_length = int(audio.info.length)

		song_id = db.save_song(form.song_name.data, song_length, form.track_number.data, form.album_name.data, form.album_release_year.data, form.artist_name.data)
		song = db.get_song_by_id(song_id)

		flash(upload_file(BUCKET_NAME, song_filename, song[5] + ".mp3")) # file uuid

		os.remove(song_filename)

	return render_template("file_upload_to_s3.html", form=form)


# DEPRECATED
def genHeader(sample_rate, bits_per_sample, channels, samples):
	#datasize = samples * channels * bitsPerSample // 8
	#filesize = sampleRate * channels * bitsPerSample // 8 * length
	#datasize = samples * 8
	datasize = 2000*10**6
	o = bytes("RIFF",'ascii')                                               	# (4byte) Marks file as RIFF
	o += (datasize + 36).to_bytes(4,'little')                               	# (4byte) File size in bytes excluding this and RIFF marker
	o += bytes("WAVE",'ascii')                                              	# (4byte) File type
	o += bytes("fmt ",'ascii')                                              	# (4byte) Format Chunk Marker
	o += (16).to_bytes(4,'little')                                          	# (4byte) Length of above format data
	o += (1).to_bytes(2,'little')                                           	# (2byte) Format type (1 - PCM)
	o += (channels).to_bytes(2,'little')                                    	# (2byte)
	o += (sample_rate).to_bytes(4,'little')                                 	# (4byte)
	o += (sample_rate * channels * bits_per_sample // 8).to_bytes(4,'little')  	# (4byte)
	o += (channels * bits_per_sample // 8).to_bytes(2,'little')               	# (2byte)
	o += (bits_per_sample).to_bytes(2,'little')                               	# (2byte)
	o += bytes("data",'ascii')                                              	# (4byte) Data Chunk Marker
	o += (datasize).to_bytes(4,'little')                                    	# (4byte) Data size in bytes
	return o

wav_header = genHeader(RATE, BITS_PER_SAMPLE, CHANNELS, SAMPLES)

# DEPRECATED
@app.route("/audio")
def audio():
	track_index = request.args.get('track')
	if not track_index:
		track_index = 0
	else:
		track_index = int(track_index)

	audioPaths = [
		"/Users/akeeler/Polygondwanaland-WAV/1-crumbling-castle.wav",
		"/Users/akeeler/Polygondwanaland-WAV/2-polygondwanaland.wav",
		"/Users/akeeler/Polygondwanaland-WAV/3-the-castle-in-the-air-test1.wav",
		"/Users/akeeler/Polygondwanaland-WAV/4-deserted-dunes-welcome-weary-feet.wav",
		"/Users/akeeler/Polygondwanaland-WAV/5-inner-cell.wav",
		"/Users/akeeler/Polygondwanaland-WAV/6-loyalty.wav",
		"/Users/akeeler/Polygondwanaland-WAV/7-horology.wav",
		"/Users/akeeler/Polygondwanaland-WAV/8-tetrachromacy.wav",
		"/Users/akeeler/Polygondwanaland-WAV/9-searching.wav",
		"/Users/akeeler/Polygondwanaland-WAV/10-the-fourth-color.wav"
	]

	wave_file = PyWave.open(audioPaths[track_index], mode = 'r', channels = CHANNELS, frequency = RATE, bits_per_sample = BITS_PER_SAMPLE, format = PyWave.WAVE_FORMAT_PCM)

	# parse headers to get start & end of chunk
	range_header = request.headers['Range']
	start = 0
	end = wave_file.bits_per_sample * SAMPLES // 8 # number of bytes in sample
	data_length = wave_file.bits_per_sample * wave_file.samples * wave_file.channels // 8 + len(wav_header) # number of bytes in file
	if range_header: # Example header: "Range: bytes=0-1024"
		start_parsed = range_header[range_header.index('=') + 1 : range_header.index('-')]
		if start_parsed != '':
			start = int(start_parsed)
			end += start
		if (range_header.index('-') < len(range_header) - 1):
			end_parsed = range_header[range_header.index('-') + 1]
			end = int(end_parsed)

	# return audio data chunk
	if start == 0: # send header at beginning of song
		data = wav_header + wave_file.read_samples(SAMPLES)
		end += len(wav_header)
	else:
		wave_file.seek(start - len(wav_header))
		data = wave_file.read_samples(SAMPLES)

	if (start + len(data) < end):
		end = start + len(data)

	http_status = 206 # HTTP 206, Partial Content
	if (end == data_length): # return 200 for last chunk
		http_status = 200 # HTTP 200, OK

	response = Response(data, mimetype='audio/x-wav', status=http_status) # HTTP status 206, Partial Content

	# set up response headers for streaming, required for partial content
	response.headers['Accept-Range'] = "bytes"
	response.headers['Content-Type'] = "audio/x-wav"
	response.headers['Content-Range'] = "bytes " + str(start) + '-' + str(end) + '/' + str(data_length)
	response.headers['Content-Length'] = str(end - start)

	return response

@app.route("/audio-source")
def get_audio_source():

	song_id = request.args.get('song_id')
	song = db.get_song_by_id(song_id)

	if (song == None):
		return ""

	filepath = song[5] + ".mp3"

	return create_presigned_url(BUCKET_NAME, filepath)

@app.route("/generate-playlist-queue-json")
def get_playlist_queue_json():

	playlist_id = request.args.get('playlist_id')
	shuffle = (request.args.get('shuffle') == "true")
	group_songs = True

	queue = db.generate_playlist_queue(playlist_id, shuffle=shuffle, group_songs=group_songs)

	json_str = json.dumps(queue, default=str)
	return json_str

@app.route("/get-all-songs-json")
def get_all_songs_json():
	songs = db.get_all_songs_loaded()

	json_str = json.dumps(songs, default=str)
	return json_str
