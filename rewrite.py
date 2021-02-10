from dearpygui.core import *
from dearpygui.simple import *
import cv2
import json
import os
import sys
from colorama import Fore, init
from time import time, gmtime
from threading import Thread
from math import sqrt

from video_cap import get_image, begin_red_dot_timelapse, begin_viewer, begin_timelapse

#region funcs


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


#endregion

def print_stamped(text, last_stamp=-1):
    time_stamp = gmtime(time())

    if not last_stamp is -1:
        delta_time = f' | Time since last report {round(time() - last_stamp, 3)} seconds'
    else:
        delta_time = ''

    print(f'{time_stamp.tm_hour:02}:{time_stamp.tm_min:02}:{time_stamp.tm_sec:02} | {Fore.GREEN + text + Fore.RESET}' + delta_time)

class Camera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.set_resolution(get_value('tupleprevRes'))

        self.frame_count = 0
        self.last_stamp = -1

        self.update_search_settings()

        self.cwd = ''

    def update_search_settings(self):
        self.search_color = get_value('sampledColor')
        self.search_pos_x = int(get_value('xPos') * get_value('tupleprevRes')[0])
        self.search_pos_y = int(get_value('yPos') * get_value('tupleprevRes')[1])

    def set_resolution(self, res):
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, res[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, res[1])
    
    def reset_frame_count(self):
        self.frame_count = 0

    def capture_frame(self):
        self.set_resolution(get_value('tupleimgRes'))
        _, frame = self.cap.read()
        self.set_resolution(get_value('tupleprevRes'))

        filepath = os.path.join(self.cwd, f'frame-{self.frame_count:05}.png')
        cv2.imwrite(filepath, frame)

        self.frame_count += 1
        print_stamped(f'Saved: {filepath}')

    def get_image(self):
        """
        saves a still frame from the web cam
        """
        _, frame = self.cap.read()
        cv2.imwrite('save_files/out.jpg', frame)

    def get_current_color(self, frame):
        return [int(i) for i in frame[int(self.search_pos_y)][int(self.search_pos_x)][::-1]]

    def get_change(self, current_color):
        return int(sum((abs(current_color[0] - self.search_color[0]), abs(current_color[1] - self.search_color[1]), abs(current_color[2] - self.search_color[2]))))

    def create_dir(self):
        if not os.path.exists('Timelapses/'):
            os.mkdir('Timelapses/')
        
        self.cwd = f'Timelapses/Timelapse-{int(time())}'
        os.mkdir(self.cwd)

    def hms_to_sec(self, hhmmss):
        hrs, min, sec = hhmmss
        return (hrs * 60 * 60) + (min * 60) + sec


    def red_dot(self):
        new_thread = Thread(target=self.red_dot_worker)
        new_thread.daemon = True
        new_thread.start()

    def red_dot_worker(self):
        self.create_dir()

        frame_lock = False
        await_time = -1

        while True:
            _, frame = self.cap.read()

            current_color = self.get_current_color(frame)
            change = self.get_change(current_color)

            cv2.imshow('Red-Dot Timelapse', frame)

            if change < get_value('sensitivity')**2:
                if not frame_lock:
                    print_stamped('Starting to take picture')
                    await_time = time() + get_value('pictureDelay')
                    self.search_color = current_color.copy()
                    frame_lock = True
            else:
                frame_lock = False
            
            if await_time != -1 and time() > await_time:
                self.capture_frame()
                await_time = -1

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def viewer(self):
        new_thread = Thread(target=self.viewer_worker)
        new_thread.daemon = True
        new_thread.start()

    def viewer_worker(self):
        start_text_y = 20
        self.text_y = start_text_y
        d_text_y = 30
        font_scale = 0.7
        def put_text(text, frame):
            frame = cv2.putText(frame, text, (10, self.text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 255), 2)
            self.text_y += d_text_y

            return frame

        width, height = get_value('tupleprevRes')

        while True:
            _, frame = self.cap.read()

            current_color = self.get_current_color(frame)
            change = self.get_change(current_color)

            cx = int(width / 2)
            cy = int(height / 2)
            cs = 50
            frame = cv2.line(frame, (cx - cs, cy), (cx + cs, cy), (0, 0, 0), 1)
            frame = cv2.line(frame, (cx, cy - cs), (cx, cy + cs), (0, 0, 0), 1)

            self.text_y = start_text_y
            frame = put_text(f'Change: {int(sqrt(change))} | Sensitivity: {get_value("sensitivity")}', frame)
            frame = put_text(f'Sample Col: {current_color}', frame)
            frame = put_text(f'Sample Col: {self.search_color}', frame)
            frame = cv2.circle(frame, (self.search_pos_x, self.search_pos_y), 5, (0, 0, 0), 2)

            cv2.imshow('Viewer', frame)

            # await a Q press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def timed(self):
        new_thread = Thread(target=self.timed_worker)
        new_thread.daemon = True
        new_thread.start()

    def timed_worker(self):
        total_seconds_elapse = self.hms_to_sec(get_value('totalPrintTime'))
        frame_await = self.hms_to_sec(get_value('timeBetweenFrames'))

        end_time = time() + total_seconds_elapse
        next_frame = time() + frame_await

        self.create_dir()

        while True:
            # capture a frame
            _, frame = self.cap.read()

            # display frame
            cv2.imshow('Timed Timelapse', frame)

            if time() > next_frame:
                print_stamped('Starting to capture frame')
                self.capture_frame()
                next_frame = time() + frame_await

            if time() > end_time:
                break

            # await a Q press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

class App:
    def __init__(self):
        self.main_menu_btn_width = 300
        self.win_pos = (350, 50)
        
        self.create_defaults()
        self.load_settings()

        self.camera = Camera()

        self.create_main_menu()
        self.create_timelapses_win()
        self.create_red_dot_settings_win()
        self.create_timed_settings_win()

        self.create_preview()

    def start(self):
        set_main_window_size(1000, 600)
        start_dearpygui(primary_window='win_mainMenu')

    #region SETTINGS
    def create_defaults(self):
        """
        create space in memory for settings and asign default values
        """
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

    def load_settings(self):
        """
        loads the settings file (if exists) else creates the file and sets default values
        """
        # check if save files dir exists
        if not os.path.exists('save_files'):
            os.mkdir('save_files')

        # see if file exists
        if os.path.exists('save_files/settings.json'):
            # if file exists load it
            settings = json.load(open('save_files/settings.json', 'r'))
        else:
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

    def save_settings(self):
        """
        saves settings to a json file
        """
        self.camera.update_search_settings()

        settings = {
            "searchPos": [get_value('xPos'), get_value('yPos')],
            "sampledColor": get_value('sampledColor'),
            "sensitivity": get_value('sensitivity'),
            "pictureDelay": get_value('pictureDelay'),
            "tupleprevRes": get_value('tupleprevRes'),
            "tupleimgRes": get_value('tupleimgRes'),
        }
        json.dump(settings, open('save_files/settings.json', 'w'))

    #endregion

    #region WINDOWS
    def create_main_menu(self):
        show_timelapses_win = lambda : show_item('win_timelapses')
        show_rd_win = lambda : show_item('win_redDotSettings')
        show_ttl_win = lambda : show_item('win_ttlSettings')

        with window('win_mainMenu', label='Main Menu', x_pos=self.win_pos[0], y_pos=self.win_pos[1]):
            add_button('showTimelapsesWin', label='Timelapses', width=self.main_menu_btn_width, callback=show_timelapses_win, tip='Show the Timelapses window')
            add_button('showRDWin', label='Red Dot Settings', width=self.main_menu_btn_width, callback=show_rd_win, tip='Show the Red-Dot settings')
            add_button('showTTLWin', label='Timed Time-lapse Settings', width=self.main_menu_btn_width, callback=show_ttl_win, tip='Show the Timed Timelapse settings')

            add_dummy(height=50)
            add_button('saveButton', label='Save Settings', width=self.main_menu_btn_width, callback=self.save_settings, tip='Save all current settings')

            add_dummy(height=200)
            add_button('exitButton', label='Exit', width=self.main_menu_btn_width, callback=self.kill, tip='Perform a clean exit without saving (cleans up some temporary files)')


    def create_timelapses_win(self):
        with window('win_timelapses', label='Timelapses', autosize=True, show=False, x_pos=self.win_pos[0], y_pos=self.win_pos[1]):
            """
            timelapse settings
            """
            add_button('startViewer', label='Start Viewer', callback=self.camera.viewer, tip='Start the viewer, used to calibrate sensitivity')
            add_button('startRedDot', label='Start Red Dot', callback=self.camera.red_dot, tip='Start the red-dot searching timelapse with current settings')
            add_button('startTimed', label='Start Timed Time-Lapse', callback=self.camera.timed, tip='Start the Timed time-lapse with current settings')

            add_input_int2('prevRes', label='Preview Resolution', source='tupleprevRes', tip='Preview resolution, keep this value very low for best results')
            add_input_int2('imgRes', label='Image Resolution', source='tupleimgRes', tip='Image resolution, if your output is black, it\'s possible your camera does not\nsupport the resolution')

    def create_red_dot_settings_win(self):
        show_imgprev_win = lambda : show_item('imgPreview')

        with window('win_redDotSettings', label='Red Dot Settings', show=False, x_pos=self.win_pos[0], y_pos=self.win_pos[1], width=450, height=250):
            """
            recognition settings
            """
            add_button('btn_showPrev', label='Show Preview', callback=show_imgprev_win, tip='Display a preview of the web cam image with the position of the search pixel overlaid')

            add_input_float('xFinder', label='X Search Position', max_value=1, max_clamped=True, min_clamped=True, callback=self.update_circle_pos, source='xPos', step=0.001, tip='X position of the search pixel')
            add_input_float('yFinder', label='Y Search Position', max_value=1, max_clamped=True, min_clamped=True, callback=self.update_circle_pos, source='yPos', step=0.001, tip='Y position of the search pixel')

            add_input_int('sensInp', label='Sensitivity', source='sensitivity', min_value=0, max_value=255, min_clamped=True, max_clamped=True, tip='The sensitivity of the search, decrease value if you are getting false positives\nand increase if software does not recognise the dot')
            add_input_float('picDelay', label='Capture Delay', source='pictureDelay',min_value=0, max_value=5, min_clamped=True, max_clamped=True, tip='The delay (in seconds) between dot recognition and capture of frame, increase if timelapses are jittery')

            add_button('btn_sampleCol', label='Sample Color', callback=self.sample_color, tip='Get the colour to search for')

            add_child('colourDisplayHolder', border=False)

            add_drawing('colourDisplayer', width=50, height=50)
            draw_rectangle('colourDisplayer', [0, 0], [50, 50], get_value('sampledColor'), fill=get_value('sampledColor'), tag='rect##dynamic')

            text = 'Not Sampled' if get_value('sampledColor') == [0, 0, 0] else str(get_value('sampledColor'))
            add_text('colourDisplayText', default_value=text,parent='colourDisplayHolder')
            end()

    def create_timed_settings_win(self):
        with window('win_ttlSettings', label='Timed Time-lapse Settings', autosize=True, show=False, x_pos=self.win_pos[0], y_pos=self.win_pos[1]):
            """
            timed time-lapse settings
            """

            add_input_int3('printTime', label='Total Print Time', source='totalPrintTime', callback=self.calculate_per_print, tip='How long your print will take (roughly is okay),\nthis value will be used to exit the timelapse after the time has expired HH:MM:SS')
            add_input_int3('timeBetweenFrames', label='Time Between Frames', source='timeBetweenFrames', callback=self.calculate_per_print, tip='Time to wait between each frame HH:MM:SS')
            add_text('timelapseInfoText', default_value='', source='calculatedInfo')


    def create_preview(self):
        with window('imgPreview', label='Image Preview', autosize=True, show=False, x_pos=0, y_pos=0):
            """
            display camera image
            """
            add_button('btn_updatePreview', label='Update Preview Image', width=640, callback=self.update_preview_image)

            add_drawing('draw_prevImage', width=640, height=480)
            self.update_preview_image()

    #endregion

    def kill(self):
        """
        kills the program
        """
        self.clean_up()
        sys.exit(0)

    def update_circle_pos(self):
        """
        Updates the search circle on the main screen when position is changed
        """
        x = get_value('xPos')
        y = get_value('yPos')

        modify_draw_command('draw_prevImage', 'circle##dynamic', center=[640*x, 480*y])

    def update_preview_image(self):
        self.camera.get_image()
        delete_item('draw_prevImage')
        add_drawing('draw_prevImage', width=640, height=480, parent='imgPreview')

        draw_image('draw_prevImage', 'save_files/out.jpg', [0, 0], [640, 480])

        x = get_value('xPos')
        y = get_value('yPos')
        draw_circle('draw_prevImage', [640*x, 480*y], 5, [255, 255, 255, 255], tag='circle##dynamic')

        self.update_circle_pos()

    def calculate_per_print(self):
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

        set_value('calculatedInfo', f'Waiting this amount will result in {total_frames} frames during this print\nAt 30fps this will result in a {timelapse_elapse} seconds long time-lapse')

    def sample_color(self):
        """
        Samples the colour defined by the circle
        """

        # read the image
        img = cv2.imread('save_files/out.jpg', cv2.IMREAD_COLOR)

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

    def clean_up(self):
        self.camera.cap.release()
        cv2.destroyAllWindows()
        os.remove('save_files/out.jpg')


if __name__ == '__main__':
    os.system('cls')

    init()

    app = App()
    app.start()

