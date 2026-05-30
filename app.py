from flask import Flask, render_template, jsonify, request, Response
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import requests
import urllib.parse
import random
import os
import json

BLOOMIN8_IP = "192.168.1.104"
CACHE_FILE = "gallery_cache.json"

def fetch_full_gallery(gallery_name):
    """Loops through Bloomin8 API until 'more' is false."""
    all_images = []
    offset = 0
    has_more = True

    while has_more:
        url = f"http://{BLOOMIN8_IP}/gallery"
        params = {
            "gallery_name": gallery_name,
            "offset": offset,
            "limit": 50,
            "full": 1
        }
        
        response = requests.get(url, params=params, timeout=50)
        response.raise_for_status()
        data = response.json()
        
        batch = data.get('data', [])
        all_images.extend(batch)

        print('more!?')
        print(data)
        print(data.get('more', False))
        
        has_more = data.get('more', False)
        
        if has_more:
            offset += len(batch)
            
    return all_images

app = Flask(__name__)

@app.route("/")
def home():
    return render_template('ascii-render.html')

@app.route("/api/bloomin/device_info")
def bloomin__device_info():
    response = requests.get('http://192.168.1.104/deviceInfo')
    json = response.json()
    return jsonify(json), 200

@app.route("/api/bloomin/get_pull_config")
def bloomin__get_pull_config():
    response = requests.get('http://192.168.1.104/upstream/pull_settings')
    json = response.json()

    device_time = datetime.fromtimestamp(json['time'])
    next_time = datetime.fromtimestamp(json['next_cron_time'])

    return jsonify({
        'upstream_on': json['upstream_on'],
        'upstream_url': json['upstream_url'],
        'device_time': device_time.isoformat(),
        'next_time': next_time.isoformat(),
        'seconds_until_next': f"{int((next_time - device_time).total_seconds())} seconds",
        'minutes_until_next': f"{int((next_time - device_time).total_seconds() / 60)} mins"
    }), 200

@app.route("/api/bloomin/pull_config/set_upstream", methods=['PUT'])
def bloomin__set_pull_config():
    data = request.get_json()
    payload = {
        'upstream_url': data['upstream_url']
    }
    requests.put('http://192.168.1.104/upstream/pull_settings', json=payload)
    return Response(status=200)


@app.route("/api/bloomin/pull_config/set_upstream_on", methods=['PUT'])
def bloomin__set_upsteam_on():
    data = request.get_json()

    now_utc = datetime.now(timezone.utc)
    future_utc = now_utc + timedelta(minutes=60)

    payload = {
        'upstream_on':  data['enabled'],
        'cron_time': future_utc.isoformat()
    }
    requests.put('http://192.168.1.104/upstream/pull_settings', json=payload)
    return Response(status=200)

@app.route("/eink_pull")
def eink_pull():
    gallery_name = request.args.get('gallery', 'default')
    force_refresh = request.args.get('force', 'false').lower() == 'true'
    
    full_list = None

    # 1. Try to load from Cache first (unless forcing a refresh)
    if os.path.exists(CACHE_FILE) and not force_refresh:
        try:
            with open(CACHE_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    full_list = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            # If file is empty or corrupted, we'll just refetch
            full_list = None

    # 2. Fetch from network if cache is empty/missing/forced
    if not full_list:
        try:
            full_list = fetch_full_gallery(gallery_name)
            
            # Save the new list to cache
            with open(CACHE_FILE, 'w') as f:
                json.dump(full_list, f)
        except Exception as e:
            return jsonify({
                "error": "Failed to reach Bloomin8 device",
                "details": str(e)
            }), 500

    # 3. Handle empty gallery case
    if not full_list:
        return jsonify({"error": "Gallery is empty"}), 404

    # 4. Pick a random winner
    random_image = random.choice(full_list)
    
    return jsonify({
        "selection": random_image,
        "total_images": len(full_list),
        "cached": not force_refresh and full_list is not None
    })


@app.route("/api/torrent/search/<query>")
def torrent_search(query):
    response = requests.get('https://thepiratebay.org/search.php?q=' + urllib.parse.quote(query) + '&all=on&search=Pirate+Search&page=0')
    print(response)
    return jsonify({ "status": 'ok'}), 200