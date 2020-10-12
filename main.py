from os import system ; system('cls')
from time import time
from timelapse import TimeLapse

timelapse = TimeLapse()
timelapse_type = 0
timelapse_types = [timelapse.timed_timelapse, timelapse.dot_search_timelapse]

while True:
    if (result := timelapse.settings())[0]:
        timelapse_type = result[1]
        break

while timelapse.active:
    timelapse.update_frame()
    timelapse.display_latest_frame()

    timelapse.quit_on_button_press()

    timelapse_types[timelapse_type]()




