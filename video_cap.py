import numpy as np
import cv2
import json
from threading import Thread
import os
from time import time
from vector_class import Vector3D as Vec


def get_image():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    _, frame = cap.read()

    cv2.imwrite('out.jpg', frame)

    cap.release()
    cv2.destroyAllWindows()


def timelapse_worker():
    try:
        settings = json.load(open('save_files/settings.json', 'r'))
    except FileNotFoundError:
        return

    search_x, search_y = settings.get('searchPos')
    search_x = int(search_x * 640)
    search_y = int(search_y * 480)
    search_color = Vec(settings.get('sampleCol'))

    cwdir = f'Timelapses/Timelapse-{int(time())}'
    os.mkdir(cwdir)
    frames = 0
    frame_lock = False
    dchange = 50

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    while True:
        _, frame = cap.read()

        cv2.imshow('Timelapse on-going', frame)

        color = Vec(list(frame[search_y][search_x]))
        if sum((search_color - color).get()) < dchange:
            if not frame_lock:
                cv2.imwrite(os.path.join(
                    cwdir, f'frame-{frames:05}.png'), frame)
                frames += 1
                frame_lock = True
        else:
            frame_lock = False

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def begin_timelapse():
    new_thread = Thread(target=timelapse_worker)
    new_thread.daemon = True
    new_thread.start()
