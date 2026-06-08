import requests
from config import BLOOMIN8_IP

def fetch_full_gallery(gallery_name):
    all_images = []
    offset = 0
    has_more = True

    while has_more:
        url = f"http://{BLOOMIN8_IP}/gallery"
        params = {"gallery_name": gallery_name, "offset": offset, "limit": 50, "full": 1}
        response = requests.get(url, params=params, timeout=50)
        response.raise_for_status()
        data = response.json()
        batch = data.get('data', [])
        all_images.extend(batch)
        has_more = data.get('more', False)
        if has_more:
            offset += len(batch)

    return all_images