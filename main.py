import asyncio
import cv2
import datetime
from time import sleep, time

import numpy as np
from uiprotect import ProtectApiClient
from uiprotect.data import EventType
from uiprotect.data import WSSubscriptionMessage

fps = 2
width = 1280
height = 720
host = "your-ui-protect-ip-here"
port = 443
username = "yourusernamehere"
password = "yourpasswordhere"

texts = [
    'No Events',
    'No Events',
    'No Events'
]

stream_urls = [
    'rtsp://mediamtx-host-ip:8554/events1',
    'rtsp://mediamtx-host-ip:8554/events2',
    'rtsp://mediamtx-host-ip:8554/events3'
]

outs = [
    cv2.VideoWriter('appsrc ! videoconvert' + \
                    ' ! video/x-raw,format=I420' + \
                    ' ! x264enc speed-preset=ultrafast bitrate=600 key-int-max=' + str(fps * 2) + \
                    ' ! video/x-h264,profile=baseline' + \
                    ' ! rtspclientsink location=' + stream_url,
                    cv2.CAP_GSTREAMER, 0, fps, (width, height), True)
    for stream_url in stream_urls
]

for i, out in enumerate(outs):
    if not out.isOpened():
        raise Exception(f"Can't open video writer for stream {i + 1}")


def display_image_with_text(frame, image_bytes, text):
    # Convert bytes to image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Resize image to fit the entire frame
    resized_img = cv2.resize(img, (width, height))

    # Place the resized image in the frame
    frame[0:height, 0:width] = resized_img

    # Add text at the bottom right of the frame
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
    text_x = width - text_size[0] - 10  # Small margin from the right edge
    text_y = height - 10  # Small margin from the bottom edge
    cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)


images = [b'', b'', b'']
times = [None, None, None]



def update_image(bytes: bytes):
    global images
    images.insert(0, bytes)
    if len(images) >=3:
        images.pop(3)


with open("none.jpg", "rb") as no_image_yet:
    y = no_image_yet.read()
    for x in range(3):
        update_image(y)

def changetext(text: str):
    global texts
    texts.insert(0, text)
    if len(texts) >=3:
        texts.pop(3)

def append_timestamp(timestamp: datetime.datetime):
    global times
    times.insert(0, timestamp)
    if len(times) >=3:
        times.pop(3)

def get_image_bytes(id):
    return images[id]


def video_streaming_loop():
    start = time()

    while True:
        for i in range(3):
            frame = np.zeros((height, width, 3), np.uint8)

            display_image_with_text(frame, get_image_bytes(int(i)), texts[i] + (" - Time Since Event: " + calculate_time_since(times[i]) if times[i] is not None else ""))

            outs[i].write(frame)

        now = time()
        diff = (1 / fps) - (now - start)
        if diff > 0:
            sleep(diff)
        start = now


protect = ProtectApiClient(host, port, username, password, verify_ssl=False)


event = asyncio.Event()
events = []
def calculate_time_since(datetime_object):
    now = datetime.datetime.now(datetime.timezone.utc)
    time_difference = now - datetime_object
    days = time_difference.days
    seconds = time_difference.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return str(f"{days}d {hours}h {minutes}m {seconds}s")


async def main():
    await protect.update()

    async def get_event_pic(id, text, timestamp):
        pic = await protect.get_event_thumbnail(id, retry_timeout=100)
        update_image(pic)
        changetext(str(text))
        append_timestamp(timestamp)

    def callback(msg: WSSubscriptionMessage):
        if hasattr(msg, "changed_data"):
            if "type" in msg.changed_data:
                if msg.changed_data["type"] is not None:
                    print(msg)
                    print(msg.changed_data["type"])
                    changedtype = msg.changed_data["type"]
                    if changedtype == EventType.RING or changedtype == EventType.SMART_DETECT:
                        print("event")
                        timestamp = msg.changed_data['start']
                        print(type(timestamp))
                        text_to_display = protect.bootstrap.get_device_from_id(msg.changed_data["camera_id"]).name + " - Type: " + ("Smart Detection" if changedtype == EventType.SMART_DETECT else ("Doorbell Ring" if changedtype == EventType.RING else "Unknown"))
                        print(text_to_display)
                        asyncio.create_task(get_event_pic(msg.changed_data["id"], text_to_display, timestamp))

    # protect.bootstrap.cameras[msg.changed_data["camera_id"]].name
    unsub = protect.subscribe_websocket(callback)

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        unsub()
        await protect.close_session()

if __name__ == '__main__':
    import threading

    video_thread = threading.Thread(target=video_streaming_loop)
    video_thread.start()

    unifi_thread = threading.Thread(target=asyncio.run(main()))
    unifi_thread.start()

