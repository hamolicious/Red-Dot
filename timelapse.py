import numpy as np
import cv2
from os import path
from time import time
from math import sqrt
from os import system, path

class TimeLapse:
    def __init__(self):
        # -----------Flags--------------------------------
        self.active = False

        # -----------Video Capture------------------------
        self.cap = cv2.VideoCapture(0)
        self.await_cap_open()

        # -----------Frame Management---------------------
        self.latest_frame = None
        self.current_frame = 0
        self.save_dir = './'
        self.frame_lock = False
        self.dot_noise_timer_default = 100
        self.dot_noise_timer = self.dot_noise_timer_default

        # -----------Screen Management--------------------
        self.screen_name = 'Time Lapse Viewer'
        self.window_created = False

        # -----------Mouse Management---------------------
        self.mouse_pos = (0, 0)
        cv2.setMouseCallback(self.screen_name, self.mouse_input_handling)

        # -----------Search Rectangle Management----------
        self.bounding_box = []
        self.center_pixel = None
        self.dot_in_view = False
        self.search_colour = (255, 0, 0)
        self.threshhold = 200

        # -----------Output Management--------------------
        self.on_picture_output = lambda : print(f'{int(time())}   |   Picute Taken Frame: {self.current_frame:05}')

        # -----------Print Management---------------------
        self.print_time = 0

        # -----------Time Management----------------------
        self.timelapse_length = 60
        self.frame_rate = 60

        self.end_time = time() + self.print_time
        self.time_between_frames = self.print_time / (self.timelapse_length * self.frame_rate)
        self.next_frame = time() + self.time_between_frames

    def create_window(self):
        if not self.window_created:
            cv2.namedWindow(self.screen_name)
            self.window_created = True

    def mouse_input_handling(self, event, x, y, flags, param):
        self.mouse_pos = (x, y)

        if event == cv2.EVENT_LBUTTONDOWN and self.mouse_pos not in self.bounding_box:
            self.bounding_box.append(self.mouse_pos)

            if len(self.bounding_box) == 2:
                top_left = self.bounding_box[0]
                bottom_right = self.bounding_box[1]

                x, y = top_left
                w, h = bottom_right ; w = abs(x - w) ; h = abs(y - h)

                self.center_pixel = (x + int(w/2), y + int(h/2))
                # self.search_colour = self.get_rgb_at(self.center_pixel[0], self.center_pixel[1])

            if len(self.bounding_box) >= 3:
                self.bounding_box = []
                self.center_pixel = None

    def await_cap_open(self):
        while not self.cap.isOpened():
            self.cap.open()
        
        self.active = True
    
    def update_frame(self):
        if not self.active : return

        ret, frame = self.cap.read()
        if not ret : raise ConnectionRefusedError('Camera did not return an image')

        self.latest_frame = frame

    def display_latest_frame(self, grey_scale=False, display_bounding_box=True):
        if not self.active : return

        self.create_window()

        colour_space = cv2.COLOR_RGB2GRAY if grey_scale else cv2.COLOR_RGB2RGBA
        frame = cv2.cvtColor(self.latest_frame, colour_space)

        if len(self.bounding_box) < 2:
            for point in self.bounding_box:
                frame = cv2.circle(frame, point, 2, (0, 0, 255), -1)
        else:
            frame = cv2.rectangle(frame, self.bounding_box[0], self.bounding_box[1], (0, 255, 0), 1)

        picture_state = (0, 255, 0) if self.is_dot_in_view() else (0, 0, 255)
        frame = cv2.circle(frame, (20, 20), 10, picture_state, -1)
        
        cv2.imshow(self.screen_name, frame)

    def quit_on_button_press(self, key='q'):
        if cv2.waitKey(1) & 0xFF == ord(key):
            self.clean_up()

    def clean_up(self):
        self.active = False
        self.cap.release()
        cv2.destroyAllWindows()

    def get_image_size(self):
        if not self.active : return

        return (self.cap.get(3), self.cap.get(4))

    def save_frame(self):
        get_file_name = lambda : f'frame-{self.current_frame:05}.png'
        cv2.imwrite(path.join(self.save_dir, get_file_name()), self.latest_frame)

        self.on_picture_output()

        self.current_frame += 1

    def get_mouse_pos(self):
        return self.mouse_pos

    def get_rgb_at(self, x, y):
        frame = cv2.cvtColor(self.latest_frame, cv2.COLOR_RGB2RGBA)

        return (frame[y, x, 2], frame[y, x, 1], frame[y, x, 0])

    def is_dot_in_view(self):
        if self.center_pixel is None : return False

        x, y = self.center_pixel
        r1, g1, b1 = self.get_rgb_at(x, y)
        r2, g2, b2 = self.search_colour

        return int(sqrt((r2 - r1)**2 + (g2 - g1)**2 + (b2 - b1)**2)) < int(self.threshhold)

    def dot_search_timelapse(self):
        if self.is_dot_in_view() and not self.frame_lock:
            self.save_frame()
            self.frame_lock = True
        
        if not self.is_dot_in_view() and self.dot_noise_timer <= 0:
            self.frame_lock = False
            self.dot_noise_timer = self.dot_noise_timer_default
        else:
            self.dot_noise_timer -= 1

    def timed_timelapse(self):
        if time() > self.next_frame:
            self.next_frame = time() + self.time_between_frames
            self.save_frame()

        if time() > self.end_time:
            self.active = False

    def settings(self):
        """
        Not my proudest sollution, probably will make a better one later
        """
        def print_centered(string='', characters='-', space=50):
            left_over_space = 50 - len(string)
            characters = characters * int(left_over_space/2)
            print(f'{characters}{string}{characters}')
        
        system('cls')
        print_centered('Settings')
        print('--DOT SEARCH SETTINGS--')
        print(f'1. Dot Colour: {self.search_colour} |   1 255, 255, 255')
        print(f'2. Detection Threshold: {self.threshhold}   |   2 50')

        print('\n--TIMED TIMELAPSE SETTINGS--')
        print(f'3. Print Time: {self.print_time} seconds    |   3 5:40')
        print(f'4. Desired Timelapse Length: {self.timelapse_length} seconds    |   4 120')
        print(f'5. Timelapse Framerate: {self.frame_rate}   |   5 30')
        print(f'6. Timelapse Frames Directory: {self.save_dir}   |   5 C:/DIRECTORY')


        print(f'\n\n01. Start Timed Time Lapse')
        print(f'02. Start Dot Search Time Lapse')

        print_centered()
        print('Select which setting you want to alter, followed by the new value')
        print('For example: 1 (0, 255, 0)')
        print('Print time uses a HH:MM format')

        new_setting = input('>> ').strip()
        setting = new_setting[0]

        if setting == '1':
            value = new_setting.replace('1 ', '').replace(' ', '').replace(')', '').replace('(', '')
            r, g, b = value.split(',')

            self.search_colour = (int(r), int(g), int(b))
            for i in range(3):
                if self.search_colour[i] < 0   : self.search_colour[i] = 0
                if self.search_colour[i] > 255 : self.search_colour[i] = 255

        if setting == '2':
            self.threshhold = int(new_setting.replace('2 ', ''))

        if setting == '3':
            new_setting = new_setting.replace('3 ', '')
            hours, minutes = new_setting.split(':')

            self.print_time = (int(minutes) * 60) + (int(hours) * 60 * 60)

        if setting == '4':
            self.timelapse_length = int(new_setting.replace('4 ', ''))

        if setting == '5':
            self.frame_rate = int(new_setting.replace('5 ', ''))

        if setting == '6':
            new_dir = new_setting.replace('6 ', '')
            if path.isdir(new_dir):
                self.save_dir = new_dir

        if len(new_setting) < 2 : return (False, False)

        return (new_setting[0] == '0', new_setting[1] == '2')
