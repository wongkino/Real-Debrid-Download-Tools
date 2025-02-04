from flask import Flask, request, render_template, jsonify
import os
import time
import bencodepy
import hashlib
import requests

# Real-Debrid API 設定
REAL_DEBRID_API_URL = "https://api.real-debrid.com/rest/1.0"
API_TOKEN = "YOUR_REAL_DEBRID_API_TOKEN" ##輸入你的API

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def torrent_to_magnet(file_path):
    """將 .torrent 檔案轉換為磁力連結"""
    try:
        with open(file_path, 'rb') as f:
            torrent_data = bencodepy.decode(f.read())
        info_hash = hashlib.sha1(bencodepy.encode(torrent_data[b'info'])).hexdigest()
        return f"magnet:?xt=urn:btih:{info_hash}"
    except Exception as e:
        return None

def add_magnet_to_debrid(magnet_link):
    """將磁力連結添加到 Real-Debrid"""
    try:

        response = requests.post(
            f"{REAL_DEBRID_API_URL}/torrents/addMagnet",
            headers={"Authorization": f"Bearer {API_TOKEN}"},
            data={"magnet": magnet_link},
        )
        response.raise_for_status()
        return response.json().get("id")
    except:
        return None

def select_files(torrent_id):
    """選擇所有文件以開始下載"""
    try:
        requests.post(
            f"{REAL_DEBRID_API_URL}/torrents/selectFiles/{torrent_id}",
            headers={"Authorization": f"Bearer {API_TOKEN}"},
            data={"files": "all"},
        )
        return True
    except:
        return False

def get_direct_links(torrent_id):
    """獲取直接下載連結"""
    try:
        response = requests.get(
            f"{REAL_DEBRID_API_URL}/torrents/info/{torrent_id}",
            headers={"Authorization": f"Bearer {API_TOKEN}"},
        )
        response.raise_for_status()
        return response.json().get("links", [])
    except:
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist("files")
    all_links = {}
    for file in files:
        if file and file.filename.endswith(".torrent"):
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            magnet_link = torrent_to_magnet(file_path)
            if magnet_link:
                torrent_id = add_magnet_to_debrid(magnet_link)
                if torrent_id and select_files(torrent_id):
                    time.sleep(10)
                    links = get_direct_links(torrent_id)
                    all_links[file.filename] = links
    return jsonify({"links": all_links})

@app.route('/add_magnets', methods=['POST'])
def add_magnets():
    magnet_links = request.form.get("magnet_links").split("\n")
    all_links = {}
    for magnet_link in magnet_links:
        magnet_link = magnet_link.strip()
        if magnet_link:
            torrent_id = add_magnet_to_debrid(magnet_link)
            if torrent_id and select_files(torrent_id):
                time.sleep(10)
                links = get_direct_links(torrent_id)
                all_links[magnet_link] = links
    return jsonify({"links": all_links})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
