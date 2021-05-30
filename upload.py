from flask import Flask, render_template, request
import boto3
app = Flask(__name__)
from werkzeug.utils import secure_filename


s3 = boto3.client('s3',
                    aws_access_key_id= 'AKIA3CQTC2XCS4TYY27M',
                    aws_secret_access_key= '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',
                    #aws_session_token='arn:aws:s3:::audio-upload-bucket-cs351'
                     )

BUCKET_NAME='audio-upload-bucket-cs351'

@app.route('/')  
def home():
    return render_template("file_upload_to_s3.html")

@app.route('/upload',methods=['post'])
def upload():
    if request.method == 'POST':
        img = request.files['file']
        if img:
                filename = secure_filename(img.filename)
                img.save(filename)
                s3.upload_file(
                    Bucket = BUCKET_NAME,
                    Filename=filename,
                    Key = filename
                )
                msg = "Upload Done ! "

    return render_template("file_upload_to_s3.html",msg =msg)




if __name__ == "__main__":
    
    app.run(debug=True)