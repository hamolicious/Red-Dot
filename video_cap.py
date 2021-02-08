import numpy as np
import cv2
import json
from threading import Thread
import os
from time import time


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

    search_pos = settings.get('searchPos')
    search_pos = (int(search_pos[0] * 640), int(search_pos[1] * 480))
    search_color = settings.get('sampledColor')

    return search_color, search_pos


def is_in_pos(search_color, current_color, sensitivity):
    r, g, b = search_color
    rp, gp, bp = current_color
    change = int(sum([abs(rp - r), abs(gp - r), abs(bp - b)]) / 3)
    return change < sensitivity


def save_frame(frame, frame_count, directory):
    filepath = os.path.join(directory, f'frame-{frame_count:05}.png')
    cv2.imwrite(filepath, frame)

    print(f'{time()} | Saved: {filepath}')


def timelapse_worker(sensitivity, picture_delay):
    search_color, search_pos = load_settings()

    if not os.path.exists('Timelapses/'):
        os.mkdir('Timelapses')

    cwdir = f'Timelapses/Timelapse-{int(time())}'
    os.mkdir(cwdir)
    frame_count = 0
    frame_lock = False
    await_time = -1

    inverted_color = [abs(255 - search_color[0]), abs(255 - search_color[1]), abs(255 - search_color[2])]

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    while True:
        _, frame = cap.read()
        image = cv2.circle(frame, search_pos, 5, inverted_color, 2)
        cv2.imshow('Timelapse on-going', frame)

        current_color = [int(i) for i in frame[int(search_pos[0])][int(search_pos[1])]]
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
