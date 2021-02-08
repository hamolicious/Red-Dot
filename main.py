from dearpygui.core import *
from dearpygui.simple import *
from video_cap import get_image, begin_timelapse, viewer
import cv2
import json
import os
import sys

from os import system
system('cls')


def update_image():
    """
    Updates the image on the home screen
    """
    get_image()

    x = get_value('xPos')
    y = get_value('yPos')

    draw_image('mainImage', 'out.jpg', [0, 0], [640, 480])
    draw_circle('mainImage', [640*x, 480*y], 5, [
                255, 255, 255, 255], tag='circle##dynamic')


def update_circle():
    """
    Updates the search circle on the main screen when position is changed
    """
    x = get_value('xPos')
    y = get_value('yPos')

    modify_draw_command('mainImage', 'circle##dynamic', center=[640*x, 480*y])


def sample_color():
    """
    Samples the colour defined by the circle
    """

    # read the image
    img = cv2.imread('out.jpg', cv2.IMREAD_COLOR)

    # fetch and convert the position values
    x = int(get_value('xPos') * 640)
    y = int(get_value('yPos') * 480)

    # fetch and save the colour
    colour = [int(i) for i in img[y][x][::-1]]
    set_value('sampledColor', colour)

    # update the text and colour rect on main screen
    delete_item('colourDisplayText')
    add_text('colourDisplayText', default_value=str(
        colour), parent='colourDisplayHolder')
    modify_draw_command('colourDisplayer', 'rect##dynamic', fill=colour)


def start_timelapse():
    """
    start the timelapse in video_cap.py
    """

    begin_timelapse(get_value('sensitivity'), get_value('pictureDelay'))


def save_settings():
    """
    saves settings to a json file
    """
    settings = {
        "searchPos": [get_value('xPos'), get_value('yPos')],
        "sampledColor": get_value('sampledColor'),
        "sensitivity": get_value('sensitivity'),
        "pictureDelay": get_value('pictureDelay'),
    }
    json.dump(settings, open('save_files/settings.json', 'w'))


def load_settings():
    """
    loads the settings file (if exists) else creates the file and sets default values
    """
    
    # create space in memory for settings and asign default values
    add_value('sampledColor', [0, 0, 0])
    add_value('xPos', .5)
    add_value('yPos', .5)

    add_value('sensitivity', 10)
    add_value('pictureDelay', 1.0)

    # check if save files dir exists
    if not os.path.exists('save_files'):
        os.mkdir('save_files')

    # see if file exists
    try:
        # if file exists load it
        settings = json.load(open('save_files/settings.json', 'r'))
    except FileNotFoundError:
        # else create the file and fill it with default settings
        json.dump({}, open('save_files/settings.json', 'w'))
        save_settings()
        return

    # if file loaded, fill out the memory with settings
    set_value('xPos', settings.get('searchPos')[0])
    set_value('yPos', settings.get('searchPos')[1])
    set_value('sampledColor', settings.get('sampledColor'))
    set_value('sensitivity', settings.get('sensitivity'))
    set_value('pictureDelay', settings.get('pictureDelay'))


def kill():
    """
    kills the program
    """
    sys.exit(0)


load_settings()


with window('Recognition Settings', width=600, height=210):
    """
    recognition settings
    """
    set_window_pos('Recognition Settings', 650, 220)

    add_input_float('xFinder', label='X Search Position',
                    max_value=1, max_clamped=True, min_clamped=True, callback=update_circle, source='xPos', step=0.001, tip='X position of the search pixel')
    add_input_float('yFinder', label='Y Search Position',
                    max_value=1, max_clamped=True, min_clamped=True, callback=update_circle, source='yPos', step=0.001, tip='Y position of the search pixel')

    add_button('sampleCol', label='Sample Color',
               callback=sample_color, tip='Get the colour to search for')

    add_child('colourDisplayHolder', border=False, width=600, height=100)

    add_drawing('colourDisplayer', width=50, height=50)
    draw_rectangle('colourDisplayer', [0, 0], [50, 50], get_value(
        'sampledColor'), fill=get_value('sampledColor'), tag='rect##dynamic')

    text = 'Not Sampled' if get_value('sampledColor') == [
        0, 0, 0] else str(get_value('sampledColor'))
    add_text('colourDisplayText', default_value=text,
             parent='colourDisplayHolder')
    end()

with window('Timelapse', width=600, height=200):
    """
    timelapse settings
    """
    set_window_pos('Timelapse', 650, 10)

    add_button('startRedDot', label='Start Red Dot', callback=start_timelapse,
               tip='Start the red-dot searching timelapse with current settings')
    add_button('startViewer', label='Start Viewer', callback=viewer,
               tip='Start the viewer, used to calibrate sensitivity')

    add_input_int('sensInp', label='Sensitivity', source='sensitivity',
                  min_value=0, max_value=255, min_clamped=True, max_clamped=True, tip='The sensitivity of the search, decrease value if you are getting false positives\nand increase if software does not recognise the dot')
    add_input_float('picDelay', label='Capture Delay', source='pictureDelay',
                    min_value=0, max_value=5, min_clamped=True, max_clamped=True, tip='The delay (in seconds) between dot recognition and capture of frame, increase if timelapses are jittery')

with window('Actions', width=150, height=100):
    """
    actions such as saving and quiting
    """
    set_window_pos('Actions', 650, 440)

    add_button('saveButton', label='Save Settings',
               callback=save_settings, tip='Save all current settings')
    add_button('exitButton', label='Exit',
               callback=kill, tip='Exit without saving')

with window('Video Capture', width=640, height=480):
    """
    display camera image
    """
    add_drawing('mainImage', width=640, height=480)
    update_image()

set_main_window_size(1200, 700)
start_dearpygui(primary_window='Video Capture')
