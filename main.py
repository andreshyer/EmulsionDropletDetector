from os import mkdir
from shutil import rmtree
from pathlib import Path
import threading

from cv2 import imread
from kivy import require
from kivy.uix.label import Label
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.lang.builder import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import mainthread, Clock

from Core.CircleDectector import Detector

# Define that Kivy 2.0.0 is required for code to try and run
require('2.0.0')


class FileSelector(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self, file_path):

        if file_path:
            file_path = file_path[0]
            imread(file_path)
            if imread(file_path) is not None:
                self.parent.file_path = Path(file_path)
                self.manager.screens[1].ids.file_name.text = self.parent.file_path.name
                self.parent.transition.direction = 'left'
                self.parent.current = "loading_screen"
            else:
                self.ids.dir_check.text = "File Type is not Supported"
        if not file_path:
            self.ids.dir_check.text = "File not Chosen"

    def _show_default_heading(self, dt):
        self.ids.dir_check.text = "Select Picture File to Identify Circles"

    def delete_all_data(self):
        data_dir_path = Path(__file__).parent / "AppData/data"
        rmtree(data_dir_path)
        mkdir(data_dir_path)
        self.ids.dir_check.text = "All Cached Data has been deleted"
        Clock.schedule_once(self._show_default_heading, 2)


class MainWindow(Screen, BoxLayout, GridLayout, Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load_images(self):
        self.ids.current_image.reload()
        self.ids.detected_image.reload()
        self.ids.zoomed_image.reload()

        circles_left = self.parent.circle_detector.num_of_circles
        index = self.parent.circle_detector.index
        self.ids.circle_index.text = f"{index + 1} of {circles_left} Detected Circles"

    def check_toggle_buttons(self):
        if self.parent.circle_detector.current_index_is_circle == 'yes':
            self.ids.yes_button.state = 'down'
            self.ids.no_button.state = 'normal'
        elif self.parent.circle_detector.current_index_is_circle == 'no':
            self.ids.yes_button.state = 'normal'
            self.ids.no_button.state = 'down'
        elif self.parent.circle_detector.current_index_is_circle == 'unmarked':
            self.ids.yes_button.state = 'normal'
            self.ids.no_button.state = 'normal'

    # Bottom Buttons #

    def release_next_unmarked(self):
        self.parent.circle_detector.next_unmarked(forward=True)
        self.check_toggle_buttons()
        self.load_images()

    def release_next(self):
        self.parent.circle_detector.detect_next_circle(forward=True)
        self.check_toggle_buttons()
        self.load_images()

    def release_prev(self):
        self.parent.circle_detector.detect_next_circle(forward=False)
        self.check_toggle_buttons()
        self.load_images()

    def release_prev_unmarked(self):
        self.parent.circle_detector.next_unmarked(forward=False)
        self.check_toggle_buttons()
        self.load_images()

    def press_yes(self):
        if self.ids.yes_button.state == 'down':
            self.parent.circle_detector.update_choice(choice='yes')
            self.parent.circle_detector.detect_next_circle(forward=True)
            self.ids.yes_button.state = 'normal'
            self.load_images()
        if self.ids.yes_button.state == 'normal':
            self.parent.circle_detector.update_choice(choice='unmarked')
            self.load_images()

    def press_no(self):
        if self.ids.no_button.state == 'down':
            self.parent.circle_detector.update_choice(choice='no')
            self.parent.circle_detector.detect_next_circle(forward=True)
            self.ids.no_button.state = 'normal'
            self.load_images()
        if self.ids.no_button.state == 'normal':
            self.parent.circle_detector.update_choice(choice='unmarked')
            self.load_images()

    # Top Buttons #

    def press_return(self):
        self.ids.return_image.source = str(Path("AppData/icons/pressed.jpeg"))

    def release_return(self):
        self.manager.screens[0].ids.dir_check.text = "Select Picture File to Identify Circles"
        self.ids.return_image.source = "AppData/icons/return_default.jpeg"

    def press_clear(self):
        self.ids.clear_image.source = "AppData/icons/pressed.jpeg"

    def release_clear(self):
        self.ids.clear_image.source = "AppData/icons/clear_default.jpeg"
        self.parent.circle_detector.clear_all_data()
        self.load_images()

    def press_export(self):
        self.ids.export_image.source = "AppData/icons/pressed.jpeg"

    def release_export(self):
        self.ids.export_image.source = "AppData/icons/export_default.jpeg"
        self.parent.transition.direction = 'left'
        self.parent.current = "file_exporter"


class LoadingScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load_image(self):
        threading.Thread(target=self._load_image).start()

    def _load_image(self):

        self._loading_bar()
        self.parent.circle_detector = Detector(self.parent.file_path)

        if self.parent.circle_detector.has_circles:
            self.parent.transition.direction = 'left'
            self.parent.current = "main_window"

        else:
            self.manager.screens[0].ids.dir_check.text = "No Circles detected in file"
            self.parent.transition.direction = 'right'
            self.parent.current = "file_selector"

    @mainthread
    def _loading_bar(self):
        anchor_layout = AnchorLayout()
        anchor_layout.add_widget(Image(source="AppData/icons/loading.zip",
                                       keep_data=True))
        self.add_widget(anchor_layout)


class FileExporter(Screen):

    def fetch_file_name(self):
        file_path = self.parent.circle_detector.file_path
        file_path = "".join(file_path.name.split(".")[:-1]) + ".csv"
        self.ids.file_path.text = file_path

    def release_back(self):
        self.parent.transition.direction = 'right'
        self.parent.current = "main_window"

    def export_data(self, dir_path):
        file_path = Path(dir_path)
        file_path = file_path / self.ids.file_path.text
        self.parent.circle_detector.csv_data.to_csv(file_path, index=False)
        self.release_back()


class WindowManager(ScreenManager):
    pass


class EmulsionBubbleDetectorApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.circle_detector = None
        self.file_path = None

    def build(self):
        self.icon = 'AppData/vcu_png.png'
        return kv


if __name__ == "__main__":
    kv = Builder.load_file('AppData/Dev.kv')
    EmulsionBubbleDetectorApp().run()
