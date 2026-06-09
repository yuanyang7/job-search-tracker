import json
import os
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder='.')
DATA_FILE = os.path.join(os.path.dirname(__file__), 'jobs.json')


def read_jobs():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)


def write_jobs(jobs):
    with open(DATA_FILE, 'w') as f:
        json.dump(jobs, f, indent=2)


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    return jsonify(read_jobs())


@app.route('/api/jobs', methods=['POST'])
def save_jobs():
    jobs = request.get_json()
    if not isinstance(jobs, list):
        return jsonify({'error': 'expected a list'}), 400
    write_jobs(jobs)
    return jsonify({'ok': True})


if __name__ == '__main__':
    print('Job tracker running at http://localhost:5200')
    app.run(port=5200, debug=False)
