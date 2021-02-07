from dearpygui.core import *
from dearpygui.simple import *
from video_cap import get_image, begin_timelapse
import cv2
import json
import os

from os import system
system('cls')


def update_image():
    get_image()

    x = get_value('xPos')
    y = get_value('yPos')

    draw_image('mainImage', 'out.jpg', [0, 0], [640, 480])
    draw_circle('mainImage', [640*x, 480*y], 5, [
                255, 255, 255, 255], tag='circle##dynamic')


def update_circle():
    x = get_value('xPos')
    y = get_value('yPos')

    modify_draw_command('mainImage', 'circle##dynamic', center=[640*x, 480*y])


def sample_color():
    img = cv2.imread('out.jpg', cv2.IMREAD_COLOR)
    x = int(get_value('xPos') * 640)
    y = int(get_value('yPos') * 480)

    colour = [int(i) for i in img[y][x][::-1]]
    set_value('sampledColor', colour)

    delete_item('colourDisplayText')
    add_text('colourDisplayText', default_value=str(
        colour), parent='colourDisplayHolder')
    modify_draw_command('colourDisplayer', 'rect##dynamic', fill=colour)


def start_timelapse():
    begin_timelapse(get_value('sensitivity'), get_value('pictureDelay'))


def save_settings():
    settings = {
        "searchPos": [get_value('xPos'), get_value('yPos')],
        "sampledColor": get_value('sampledColor'),
        "sensitivity": get_value('sensitivity'),
        "pictureDelay": get_value('pictureDelay'),
    }
    json.dump(settings, open('save_files/settings.json', 'w'))


def load_settings():
    add_value('sampledColor', [0, 0, 0])
    add_value('xPos', .5)
    add_value('yPos', .5)

    add_value('sensitivity', 50)
    add_value('pictureDelay', 1.0)

    if not os.path.exists('save_files'):
        os.mkdir('save_files')

    try:
        settings = json.load(open('save_files/settings.json', 'r'))
    except FileNotFoundError:
        json.dump({}, open('save_files/settings.json', 'w'))
        return

    set_value('xPos', settings.get('searchPos')[0])
    set_value('yPos', settings.get('searchPos')[1])
    set_value('sampledColor', settings.get('sampledColor'))
    set_value('sensitivity', settings.get('sensitivity'))
    set_value('pictureDelay', settings.get('pictureDelay'))


def kill():
    quit()


load_settings()


with window('Recognition Settings', width=600, height=200):
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
    add_button('startRedDot', label='Start Red Dot', callback=start_timelapse,
               tip='Start the red-dot searching timelapse with current settings')

    add_input_int('sensInp', label='Sensitivity', source='sensitivity',
                  min_value=0, max_value=255, min_clamped=True, max_clamped=True, tip='The sensitivity of the search, decrease value if you are getting false positives\nand increase if software does not recognise the dot')
    add_input_float('picDelay', label='Capture Delay', source='pictureDelay',
                    min_value=0, max_value=5, min_clamped=True, max_clamped=True, tip='The delay (in seconds) between dot recognition and capture of frame, increase if timelapses are jittery')

with window('Actions', width=100, height=100):
    add_button('saveButton', label='Save Settings',
               callback=save_settings, tip='Save all current settings')
    add_button('exitButton', label='Exit',
               callback=kill, tip='Exit without saving')

with window('Video Capture', width=640, height=480):
    add_drawing('mainImage', width=640, height=480)
    update_image()

set_main_window_size(800, 700)
start_dearpygui(primary_window='Video Capture')
