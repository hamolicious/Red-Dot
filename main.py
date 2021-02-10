from dearpygui.core import *
from dearpygui.simple import *
from video_cap import get_image, begin_red_dot_timelapse, begin_viewer, begin_timelapse
import cv2
import json
import os
import sys

os.system('cls')


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


def start_red_dot_timelapse():
    """
    start the timelapse in video_cap.py
    """

    begin_red_dot_timelapse(get_value('sensitivity'), get_value('pictureDelay'), get_value('tupleprevRes'), get_value('tupleimgRes'))


def start_viewer():
    """
    start the viewer in video_cap.py
    """

    begin_viewer(get_value('sensitivity'), get_value('tupleprevRes'))

def start_timed():
  # begin_timelapse(preview_resm, img_res, frame_every_sec, total_seconds_elpase)

    hrs, mns, sec = get_value('timeBetweenFrames')
    frame_wait = (hrs * 60 * 60) + (mns * 60) + sec

    hrs, mns, sec = get_value('totalPrintTime')
    total_sec = (hrs * 60 * 60) + (mns * 60) + sec

    begin_timelapse(get_value('tupleprevRes'), get_value('tupleimgRes'), frame_wait, total_sec)

def save_settings():
    """
    saves settings to a json file
    """
    settings = {
        "searchPos": [get_value('xPos'), get_value('yPos')],
        "sampledColor": get_value('sampledColor'),
        "sensitivity": get_value('sensitivity'),
        "pictureDelay": get_value('pictureDelay'),
        "tupleprevRes": get_value('tupleprevRes'),
        "tupleimgRes": get_value('tupleimgRes'),
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

    add_value('tupleprevRes', [640, 480])
    add_value('tupleimgRes', [1280, 720])

    add_value('timeBetweenFrames', [0,0,0])
    add_value('totalPrintTime', [0,0,0])
    add_value('calculatedInfo', '')

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

    set_value('tupleprevRes', settings.get('tupleprevRes'))
    set_value('tupleimgRes', settings.get('tupleimgRes'))


def kill():
    """
    kills the program
    """
    sys.exit(0)


def calculate_per_print():
    hrs1, mns1, sec1 = get_value('timeBetweenFrames')
    hrs2, mns2, sec2 = get_value('totalPrintTime')

    # convert time to seconds
    await_time = (sec1) + (mns1 * 60) + (hrs1 * 60 * 60)
    print_time = (sec2) + (mns2 * 60) + (hrs2 * 60 * 60)

    try:
        total_frames = int(print_time / await_time)
        timelapse_elapse = round(total_frames / 30, 3)
    except ZeroDivisionError:
        set_value('calculatedInfo', '')
        return

    set_value('calculatedInfo', f'Awaiting this amount will result in {total_frames} frames during this print\nAt 30fps this will result in a {timelapse_elapse} seconds long time-lapse')


load_settings()

with window('Timelapses', width=600, height=150):
    """
    timelapse settings
    """
    set_window_pos('Timelapses', 650, 10)

    add_button('startRedDot', label='Start Red Dot', callback=start_red_dot_timelapse,
            tip='Start the red-dot searching timelapse with current settings')
    add_button('startViewer', label='Start Viewer', callback=start_viewer,
            tip='Start the viewer, used to calibrate sensitivity')
    add_button('startTimed', label='Start Timed Time-Lapse', callback=start_timed,
            tip='Start the Timed time-lapse with current settings')

    add_input_int2('prevRes', label='Preview Resolution', source='tupleprevRes', default_value=(640, 480),
                tip='Preview resolution, keep this value very low for best results')
    add_input_int2('imgRes', label='Image Resolution', source='tupleimgRes', default_value=(640, 480),
                tip='Image resolution, if your output is black, it\'s possible your camera does not\nsupport the resolution')

with window('Red Dot Recognition Settings', width=600, height=250):
    """
    recognition settings
    """
    set_window_pos('Red Dot Recognition Settings', 650, 170)

    add_input_float('xFinder', label='X Search Position',
                    max_value=1, max_clamped=True, min_clamped=True, callback=update_circle, source='xPos', step=0.001, tip='X position of the search pixel')
    add_input_float('yFinder', label='Y Search Position',
                    max_value=1, max_clamped=True, min_clamped=True, callback=update_circle, source='yPos', step=0.001, tip='Y position of the search pixel')

    add_input_int('sensInp', label='Sensitivity', source='sensitivity',
                  min_value=0, max_value=255, min_clamped=True, max_clamped=True, tip='The sensitivity of the search, decrease value if you are getting false positives\nand increase if software does not recognise the dot')
    add_input_float('picDelay', label='Capture Delay', source='pictureDelay',
                    min_value=0, max_value=5, min_clamped=True, max_clamped=True, tip='The delay (in seconds) between dot recognition and capture of frame, increase if timelapses are jittery')

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

with window('Timed Time-lapse Settings', width=600, height=250):
    """
    timed time-lapse settings
    """
    set_window_pos('Timed Time-lapse Settings', 650, 430)

    add_input_int3('printTime', label='Total Print Time', source='totalPrintTime', callback=calculate_per_print, tip='How long your print will take (roughly is okay),\nthis value will be used to exit the timelapse after the time has expired HH:MM:SS')
    add_input_int3('timeBetweenFrames', label='Time Between Frames', source='timeBetweenFrames', callback=calculate_per_print, tip='Time to wait between each frame HH:MM:SS')
    add_text('timelapseInfoText', default_value='', source='calculatedInfo')


with window('Actions', width=150, height=100):
    """
    actions such as saving and quiting
    """
    set_window_pos('Actions', 10, 490)

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
