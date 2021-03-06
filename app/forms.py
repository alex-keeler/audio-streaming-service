from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import SubmitField, SelectField, StringField, IntegerField, HiddenField, validators
from wtforms.validators import DataRequired, Length, NumberRange, EqualTo
from decimal import ROUND_HALF_UP
from flask import flash
from app.database import db

class UploadSongForm(FlaskForm):
	song_file = FileField("Song File (.mp3): ", validators=[FileRequired()])
	song_name = StringField("Song Name: ", validators=[DataRequired()])
	artist_name = StringField("Artist Name: ", validators=[DataRequired()])
	album_name = StringField("Album Name: ")
	album_release_year = IntegerField("Album Release Year: ", [validators.optional()])
	track_number = IntegerField("Track Number: ", [validators.optional()])
	submit = SubmitField("Submit")

class AddSongToPlaylistForm(FlaskForm):
	song_id = HiddenField()
	playlist_id = SelectField("Playlist: ", validators=[DataRequired()])
	submit = SubmitField("Submit")

class CreatePlaylistForm(FlaskForm):
	playlist_name = StringField("Playlist Name: ", validators=[DataRequired()])
	submit = SubmitField("Submit")