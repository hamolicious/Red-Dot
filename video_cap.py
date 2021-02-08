import numpy as np
import cv2
import json
from threading import Thread
import os
from time import time
from math import sqrt


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
    search_color = [int(i) for i in settings.get('sampledColor')]

    return search_color, search_pos


def get_delta_col(search_color, current_color):
    r, g, b = search_color
    rp, gp, bp = current_color

    change = abs(int(r - rp) + int(g - gp) + int(b - bp))
    return change


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

        current_color = [int(i) for i in frame[int(search_pos[1])][int(search_pos[0])][::-1]]
        change = get_delta_col(search_color, current_color)

        image = cv2.circle(frame, search_pos, 5, inverted_color, 1)
        frame = cv2.putText(frame, f'Change: {change}', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (51, 70, 51), 2)

        cv2.imshow('Timelapse on-going', frame)

        if change < sensitivity**2:
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

def viewer():
    search_color, search_pos = load_settings()

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    while True:
        _, frame = cap.read()

        current_color = [int(i) for i in frame[int(search_pos[1])][int(search_pos[0])][::-1]]
        change = get_delta_col(search_color, current_color)

        frame = cv2.putText(frame, f'Change: {int(sqrt(change))}', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (51, 70, 51), 2)
        frame = cv2.putText(frame, f'Sample Col: {current_color}', (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (51, 70, 51), 2)
        frame = cv2.putText(frame, f'Sample Col: {search_color}', (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (51, 70, 51), 2)
        frame = cv2.circle(frame, search_pos, 5, (0, 0, 0), 1)

        cx = int(640 / 2) ; cy = int(480 / 2)
        cs = 50
        frame = cv2.line(frame, (cx - cs, cy), (cx + cs, cy), (0, 0, 0), 1)
        frame = cv2.line(frame, (cx, cy - cs), (cx, cy + cs), (0, 0, 0), 1)

        cv2.imshow('Viewer', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()