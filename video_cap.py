import numpy as np
import cv2
import json
from threading import Thread
import os
from time import time, gmtime
from math import sqrt
from colorama import Fore, init

init()


class TimeSave:
    last_stamp = -1


def print_stamped(text):
    time_stamp = gmtime(time())

    if not TimeSave.last_stamp is -1:
        delta_time = round(time() - TimeSave.last_stamp, 3)
    else:
        delta_time = 'N/A'

    print(f'{time_stamp.tm_hour:02}:{time_stamp.tm_min:02}:{time_stamp.tm_sec:02} | {Fore.GREEN + text + Fore.RESET} | Time since last report {delta_time} seconds')
    TimeSave.last_stamp = time()


def get_image():
    """
    saves a still frame from the web cam
    """
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    _, frame = cap.read()

    cv2.imwrite('out.jpg', frame)

    cap.release()
    cv2.destroyAllWindows()


def load_settings():
    """
    loads the settings file
    """
    try:
        settings = json.load(open('save_files/settings.json', 'r'))
    except FileNotFoundError:
        print_stamped('Settings file not found')
        return

    search_pos = settings.get('searchPos')
    search_pos = (int(search_pos[0] * 640), int(search_pos[1] * 480))
    search_color = [int(i) for i in settings.get('sampledColor')]

    return search_color, search_pos


def get_delta_col(search_color, current_color):
    """
    gets the change in colour^2
    """
    r, g, b = search_color
    rp, gp, bp = current_color

    change = abs(int(r - rp) + int(g - gp) + int(b - bp))
    return change


def save_frame(cap, frame_count, directory, preview_res, img_res):
    """
    saves a frame and displays the path in std.out
    """
    # set capture to img resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, img_res[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, img_res[1])

    # capture a frame
    _, frame = cap.read()

    # reset to preview resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, preview_res[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, preview_res[1])

    # save frame
    filepath = os.path.join(directory, f'frame-{frame_count:05}.png')
    cv2.imwrite(filepath, frame)

    print_stamped(f'Saved: {filepath}')


def create_cap(res):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, res[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, res[1])

    return cap


def red_dot_timelapse_worker(sensitivity, picture_delay, preview_res, img_res):
    """
    main timelapse thread
    """
    # load the settings
    search_color, search_pos = load_settings()

    # check if default path exists
    if not os.path.exists('Timelapses/'):
        # create if not
        os.mkdir('Timelapses')

    # save the current working directory
    cwdir = f'Timelapses/Timelapse-{int(time())}'
    os.mkdir(cwdir)

    # setup frame capturing variables
    frame_count = 0
    frame_lock = False
    await_time = -1

    # create an inverted colour for easier sight of the search circle
    inverted_color = [abs(255 - search_color[0]),
                      abs(255 - search_color[1]), abs(255 - search_color[2])]

    # create a capture object
    cap = create_cap(preview_res)

    # main loop
    while True:
        # capture a frame
        _, frame = cap.read()

        # get the colour at the search circle
        current_color = [int(i) for i in frame[int(
            search_pos[1])][int(search_pos[0])][::-1]]
        # calculate the change
        change = get_delta_col(search_color, current_color)

        # draw the circle
        image = cv2.circle(frame, search_pos, 5, inverted_color, 1)
        # display the frame
        cv2.imshow('Timelapse on-going', frame)

        # check if to capture a frame
        if change < sensitivity**2:
            # see if already capturing a frame
            if not frame_lock:
                # display the begining of a capture
                print_stamped('Starting to take picture')
                # set an await time to allow the printer to move into position
                await_time = time() + picture_delay
                # update the search colour to accomidate slight lighting changes over time
                search_color = current_color.copy()
                # set the frame lock
                frame_lock = True
        else:
            # if not ready to take picture, turn frame lock off
            frame_lock = False

        # see if time to take picture
        if await_time != -1 and time() > await_time:
            # take a picture
            save_frame(cap, frame_count, cwdir, preview_res, img_res)

            # update frame counter
            frame_count += 1
            # reset wait time
            await_time = -1

        # check if Q has been pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            # stop main loop
            break

    # destroy all windows
    cap.release()
    cv2.destroyAllWindows()


def begin_red_dot_timelapse(sensitivity, picture_delay, preview_res, img_res):
    """
    begins a new timelapse thread
    """
    new_thread = Thread(target=red_dot_timelapse_worker,
                        args=(sensitivity, picture_delay, preview_res, img_res,))
    new_thread.daemon = True
    new_thread.start()


def begin_viewer(sensitivity, preview_res):
    """
    begins a new viewer thread
    """
    new_thread = Thread(target=viewer,
                        args=(sensitivity, preview_res,))
    new_thread.daemon = True
    new_thread.start()


def viewer(sensitivity, preview_res):
    """
    a live viewer for calibration
    """
    # load settings
    search_color, search_pos = load_settings()

    # create a capture object
    width, height = preview_res
    cap = create_cap(preview_res)

    # main loop
    while True:
        # capture a frame
        _, frame = cap.read()

        # get the current colour
        current_color = [int(i) for i in frame[int(
            search_pos[1])][int(search_pos[0])][::-1]]
        # calculate change
        change = get_delta_col(search_color, current_color)

        # display information about the sensitivity
        frame = cv2.putText(frame, f'Change: {int(sqrt(change))} | Sensitivity: {sensitivity}', (
            10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (51, 70, 51), 2)
        frame = cv2.putText(frame, f'Sample Col: {current_color}', (
            10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (51, 70, 51), 2)
        frame = cv2.putText(frame, f'Sample Col: {search_color}', (
            10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (51, 70, 51), 2)
        frame = cv2.circle(frame, search_pos, 5, (0, 0, 0), 1)

        # draw a crosshair to ease aligning to center of bed
        cx = int(width / 2)
        cy = int(height / 2)
        cs = 50
        frame = cv2.line(frame, (cx - cs, cy), (cx + cs, cy), (0, 0, 0), 1)
        frame = cv2.line(frame, (cx, cy - cs), (cx, cy + cs), (0, 0, 0), 1)

        # display frame
        cv2.imshow('Viewer', frame)

        # await a Q press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # destroy all windows
    cap.release()
    cv2.destroyAllWindows()


def timelapse_worker(preview_res, img_res, frame_await, total_seconds_elapse):
    start_time = time()
    end_time = time() + total_seconds_elapse

    next_frame = time() + frame_await
    frame_count = 0

    # check if default path exists
    if not os.path.exists('Timelapses/'):
        # create if not
        os.mkdir('Timelapses')

    # save the current working directory
    cwdir = f'Timelapses/Timelapse-{int(time())}'
    os.mkdir(cwdir)

    width, height = preview_res
    cap = create_cap(preview_res)

    while True:
        # capture a frame
        _, frame = cap.read()

        # display frame
        cv2.imshow('Timelapse on-going', frame)

        if time() > next_frame:
            print_stamped('Starting to capture frame')
            save_frame(cap, frame_count, cwdir, preview_res, img_res)
            next_frame = time() + frame_await
            frame_count += 1

        if time() > end_time:
            break

        # await a Q press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # destroy all windows
    cap.release()
    cv2.destroyAllWindows()


def begin_timelapse(preview_res, img_res, frame_await, total_seconds_elapse):
    new_thread = Thread(target=timelapse_worker,
                        args=(preview_res, img_res, frame_await, total_seconds_elapse,))
    new_thread.daemon = True
    new_thread.start()
