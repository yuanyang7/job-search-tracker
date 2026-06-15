import json
import os
import re
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder='.')
DATA_FILE = os.path.join(os.path.dirname(__file__), 'jobs.json')
SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), 'snapshots')


def read_jobs():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)


def write_jobs(jobs):
    with open(DATA_FILE, 'w') as f:
        json.dump(jobs, f, indent=2)


def snapshot_path(position_id):
    # position ids are generated alphanumeric uids; strip anything else to be safe
    safe = re.sub(r'[^A-Za-z0-9_-]', '', str(position_id))
    return os.path.join(SNAPSHOT_DIR, safe + '.json')


def capture_snapshot(url):
    """Render the page in headless Chromium and return (title, readable_text)."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/120.0.0.0 Safari/537.36'
        )
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=45000)
            # give JS-rendered boards (Ashby/Workday/Greenhouse/Eightfold) time to fill in
            try:
                page.wait_for_load_state('networkidle', timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(1500)
            title = page.title()
            text = extract_text(page)
        finally:
            browser.close()
    return title, text


def extract_text(page):
    """Visible text of the main page plus any embedded job-board iframes
    (Greenhouse/Ashby widgets render the description inside an iframe)."""
    parts = []
    for frame in page.frames:
        try:
            t = frame.inner_text('body').strip()
        except Exception:
            continue
        if t and t not in parts:
            parts.append(t)
    # the richest frame is usually the job description; put longest last-ish but keep order
    return '\n\n'.join(parts)


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


@app.route('/api/snapshot', methods=['POST'])
def create_snapshot():
    data = request.get_json() or {}
    position_id = data.get('positionId')
    url = data.get('url')
    if not position_id or not url:
        return jsonify({'error': 'positionId and url are required'}), 400

    try:
        title, text = capture_snapshot(url)
    except ImportError:
        return jsonify({'error': 'Playwright is not installed. Run: '
                                 'pip install playwright && playwright install chromium'}), 500
    except Exception as e:
        return jsonify({'error': f'Could not capture the page: {e}'}), 502

    snap = {
        'url': url,
        'title': title,
        'text': text,
        'capturedAt': datetime.now().isoformat(timespec='seconds'),
    }
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    with open(snapshot_path(position_id), 'w') as f:
        json.dump(snap, f, indent=2)

    return jsonify({'title': title, 'capturedAt': snap['capturedAt'], 'chars': len(text)})


@app.route('/api/snapshot/<position_id>', methods=['GET'])
def get_snapshot(position_id):
    path = snapshot_path(position_id)
    if not os.path.exists(path):
        return jsonify({'error': 'no snapshot for this position'}), 404
    with open(path, 'r') as f:
        return jsonify(json.load(f))


if __name__ == '__main__':
    print('Job tracker running at http://localhost:5200')
    app.run(port=5200, debug=False, threaded=True)
