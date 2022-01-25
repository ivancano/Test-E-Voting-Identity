import face_recognition
import flask
from flask import request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import uuid
import os
import datetime
from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair

app = flask.Flask(__name__)
CORS(app)
app.config["DEBUG"] = True
app.config['UPLOAD_FOLDER'] = './'
bdb_root_url = 'http://143.198.189.64:9984'
bdb = BigchainDB(bdb_root_url)
alice, bob = generate_keypair(), generate_keypair()


@app.route('/', methods=['GET'])
def home():
    return "<h1>Distant Reading Archive</h1><p>This site is a prototype API for distant reading of science fiction novels.</p>"

@app.route('/api/v1/validate', methods=['POST'])
def validate():
    try:
        params = request.json
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

@app.route('/api/v1/vote', methods=['POST'])
def vote():
    try:
        params = request.json
        election_asset = {
            'data': {
                'vote': {
                    'election_detail_id': params['election_detail_id'],
                    'election_id': params['election_id'],
                    'parties_id': params['parties_id'],
                    'candidate_id': params['candidate_id'],
                    'position': params['position'],
                    'voter_id': 'voter-'+str(params['voter_id']),
                    'timestamp': datetime.datetime.now().timestamp()
                },
            },
        }
        prepared_creation_tx = bdb.transactions.prepare(
            operation='CREATE',
            signers=alice.public_key,
            asset=election_asset
        )

        fulfilled_creation_tx = bdb.transactions.fulfill(
            prepared_creation_tx,
            private_keys=alice.private_key
        )

        bdb.transactions.send_commit(fulfilled_creation_tx)
        txid = fulfilled_creation_tx['id']
        return jsonify({
            'result': txid
        })
    except Exception as e:
        print(e)
        return jsonify({
            'result': 'Error'
        })

@app.route('/api/v1/vote-count', methods=['GET'])
def vote_count():
    query_params = request.args.get('v')
    votes = []
    if(query_params):
        votes = bdb.assets.get(search='voter-'+query_params)
    else:
        votes = bdb.assets.get(search='voter-')
    print(votes)
    return jsonify({
        'result': votes
    })


if __name__ == "__main__":
    app.run(host='0.0.0.0')