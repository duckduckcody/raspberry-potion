import asyncio, httpx
from bleak import BleakClient, BleakScanner

FRAME_NAME = "Codys Canvas"
FRAME_IP = "192.168.1.104"
WRITE_CHAR = "0000fff2-0000-1000-8000-00805f9b34fb"
NOTIFY_CHAR = "0000fff1-0000-1000-8000-00805f9b34fb"
CMD = b'{"cmd":"getInfo"}\r\n'
WAKE_RETRIES = 10
WAKE_RETRY_INTERVAL = 3  # seconds between each check

def is_frame_awake():
    try:
        r = httpx.get(f"http://{FRAME_IP}/deviceInfo", timeout=2)
        return r.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False

def handle_notify(sender, data):
    print(f"Frame says: {data.decode('utf-8', errors='replace')}")

async def wait_for_frame():
    for attempt in range(1, WAKE_RETRIES + 1):
        print(f"Checking if frame is up... (attempt {attempt}/{WAKE_RETRIES})")
        if is_frame_awake():
            return True
        await asyncio.sleep(WAKE_RETRY_INTERVAL)
    return False

async def wake_frame():
    if is_frame_awake():
        return { 'status': 'frame_already_awake' }

    # Frame is asleep, scanning for BLE...
    device = await BleakScanner.find_device_by_name(FRAME_NAME, timeout=10)
    if not device:
        return { 'status': 'cannot_find_frame' }

    # found device
    async with BleakClient(device) as client:
        await client.start_notify(NOTIFY_CHAR, handle_notify)
        await client.write_gatt_char(WRITE_CHAR, CMD, response=False)
        await asyncio.sleep(5)

    if await wait_for_frame():
        print("Frame is up!")
        async with httpx.AsyncClient() as http:
            r = await http.get(f"http://{FRAME_IP}/deviceInfo")
            return { 'status': 'frame_awake' }
    else:
        return { 'status': 'frame_didnt_wake' }

