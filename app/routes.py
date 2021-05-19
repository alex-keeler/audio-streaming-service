from app import app
from flask import Flask, render_template, redirect, url_for, flash, session, Response, request
import PyWave
from app.s3storage import create_presigned_url

SAMPLES = 65536
RATE = 44100
BITS_PER_SAMPLE = 16
CHANNELS = 2
LENGTH = 15

@app.route("/")
@app.route("/index")
def index():
	return render_template("index.html")

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
	track_index = request.args.get('track')
	if not track_index:
		track_index = 0
	else:
		track_index = int(track_index)

	audio_path_lookup = [
		"Polygondwanaland-MP3/1-crumbling-castle.mp3",
		"Polygondwanaland-MP3/2-polygondwanaland.mp3",
		"Polygondwanaland-MP3/3-the-castle-in-the-air.mp3",
		"Polygondwanaland-MP3/4-deserted-dunes-welcome-weary-feet.mp3",
		"Polygondwanaland-MP3/5-inner-cell.mp3",
		"Polygondwanaland-MP3/6-loyalty.mp3",
		"Polygondwanaland-MP3/7-horology.mp3",
		"Polygondwanaland-MP3/8-tetrachromacy.mp3",
		"Polygondwanaland-MP3/9-searching.mp3",
		"Polygondwanaland-MP3/10-the-fourth-color.mp3"
	]

	return create_presigned_url('audio-test-1468', audio_path_lookup[track_index])
