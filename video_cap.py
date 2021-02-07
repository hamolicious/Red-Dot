import numpy as np
import cv2
import json
from threading import Thread
import os
from time import time
from vector_class import Vector3D as Vec3, Vector2D as Vec2


def get_image():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    _, frame = cap.read()

    cv2.imwrite('out.jpg', frame)

    cap.release()
    cv2.destroyAllWindows()


def load_settings():
    try:
        settings = json.load(open('save_files/settings.json', 'r'))
    except FileNotFoundError:
        return

    search_pos = Vec2(settings.get('searchPos'))
    search_pos.mult((640, 480))
    search_color = Vec3(settings.get('sampleCol'))

    return search_color, search_pos


def is_in_pos(search_color, current_color, sensitivity):
    change = sum((search_color - current_color).get()) / 3
    return change < sensitivity


def save_frame(frame, frame_count, directory):
    filepath = os.path.join(directory, f'frame-{frame_count:05}.png')
    cv2.imwrite(filepath, frame)

    print(f'{time()} | Saved: {filepath}')


def timelapse_worker(sensitivity, picture_delay):
    search_color, search_pos = load_settings()

    cwdir = f'Timelapses/Timelapse-{int(time())}'
    os.mkdir(cwdir)
    frame_count = 0
    frame_lock = False
    await_time = -1

    inverted_color = (Vec3(255, 255, 255) - search_color) * -1

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    while True:
        _, frame = cap.read()
        image = cv2.circle(frame, search_pos.get(), 5, inverted_color.get(), 2)
        cv2.imshow('Timelapse on-going', frame)

        current_color = Vec3(list(frame[int(search_pos.y)][int(search_pos.x)]))
        if is_in_pos(search_color, current_color, sensitivity):
            if not frame_lock:
                print(f'{time()} | Starting to take picture')
                await_time = time() + picture_delay
                search_color = current_color.copy()
                frame_lock = True
        else:
            frame_lock = False

        if await_time != -1 and time() > await_time:
            save_frame(frame, frame_count, cwdir)
            frame_count += 1

            await_time = -1

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def begin_timelapse(sensitivity, picture_delay):
    new_thread = Thread(target=timelapse_worker,
                        args=(sensitivity, picture_delay,))
    new_thread.daemon = True
    new_thread.start()
