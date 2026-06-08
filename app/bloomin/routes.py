from flask import Blueprint, jsonify, request, Response
from datetime import datetime, timedelta, timezone
import requests
from config import BLOOMIN8_IP
import asyncio
from bloomin.wake_frame import wake_frame

bloomin_bp = Blueprint('bloomin', __name__, url_prefix='/api/bloomin')

@bloomin_bp.route("/device_info")
def device_info():
    response = requests.get(f'http://{BLOOMIN8_IP}/deviceInfo')
    return jsonify(response.json()), 200

@bloomin_bp.route("/get_pull_config")
def get_pull_config():
    response = requests.get(f'http://{BLOOMIN8_IP}/upstream/pull_settings')
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

@bloomin_bp.route("/pull_config/set_upstream", methods=['PUT'])
def set_upstream():
    data = request.get_json()
    requests.put(f'http://{BLOOMIN8_IP}/upstream/pull_settings', json={'upstream_url': data['upstream_url']})
    return Response(status=200)

@bloomin_bp.route("/pull_config/set_upstream_on", methods=['PUT'])
def set_upstream_on():
    data = request.get_json()
    future_utc = datetime.now(timezone.utc) + timedelta(minutes=60)
    payload = {'upstream_on': data['enabled'], 'cron_time': future_utc.isoformat()}
    requests.put(f'http://{BLOOMIN8_IP}/upstream/pull_settings', json=payload)
    return Response(status=200)

@bloomin_bp.route("/wake_frame", methods=['PUT'])
def wake_frame_route():
    frame_status = asyncio.run(wake_frame())
    return jsonify(frame_status), 200