import face_recognition
import flask
from flask import request, jsonify
from werkzeug.utils import secure_filename
import uuid
import os

app = flask.Flask(__name__)
app.config["DEBUG"] = True
app.config['UPLOAD_FOLDER'] = './'


@app.route('/', methods=['GET'])
def home():
    return "<h1>Distant Reading Archive</h1><p>This site is a prototype API for distant reading of science fiction novels.</p>"

@app.route('/api/v1/validate', methods=['POST'])
def validate():
    try:
        params = request.form
        known_image = face_recognition.load_image_file(params['face'])
        unknown_image = face_recognition.load_image_file(params['dni'])
        biden_encoding = face_recognition.face_encodings(known_image)[0]
        unknown_encoding = face_recognition.face_encodings(unknown_image)[0]
        results = face_recognition.compare_faces([biden_encoding], unknown_encoding)
        os.remove(params['face'])
        os.remove(params['dni'])
        return jsonify({
            'result': str(results[0])
        })
    except Exception as e:
        print(e)
        return jsonify({
            'result': str(False)
        })

@app.route('/api/v1/uploader', methods=['POST'])
def upload_file():
    try:
        f = request.files['file']
        split_tup = os.path.splitext(f.filename)
        file_extension = split_tup[1]
        filename = str(uuid.uuid4()) + file_extension
        f.save(secure_filename(filename))
        return jsonify({
            'filename': filename
        })
    except Exception as e:
        print(e)
        return jsonify({
            'result': str(False)
        })

if __name__ == "__main__":
    app.run(host='0.0.0.0')