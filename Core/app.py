from shutil import rmtree, copy
from pathlib import Path
import threading
from os import mkdir
from os.path import exists
from hashlib import sha256
from json import load

from cv2 import imread, imwrite, circle
from kivy import require
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.widget import Widget
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
                self.parent.current = "prep_processing_screen"
            else:
                self.ids.dir_check.text = "File Type is not Supported"
        if not file_path:
            self.ids.dir_check.text = "File not Chosen"

    def _show_default_heading(self, dt):
        self.ids.dir_check.text = "Select Picture File to Identify Circles"

    def delete_all_data(self):
        data_dir_path = Path(__file__).parent.parent / "AppData/data"
        rmtree(data_dir_path)
        mkdir(data_dir_path)

        hashes_file_path = Path(__file__).parent.parent / "analyzed_file_hashes.txt"
        with open(hashes_file_path, "w") as f:
            pass

        self.ids.dir_check.text = "All Cached Data has been deleted"
        Clock.schedule_once(self._show_default_heading, 2)

    @staticmethod
    def get_home_path():
        return str(Path.home())


class PreProcessingScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_current_image(self):

        # Get file hash
        with open(self.parent.file_path, "rb") as f:
            file_sha256 = sha256(f.read()).hexdigest()

        # If json data exists for file, grab min and max radii
        min_radius, max_radius = 0, 0
        data_folder_path = Path(__file__).parent.parent / "AppData/data"
        opened_files = list(set([file.stem for file in data_folder_path.iterdir()]))
        if file_sha256 in opened_files:
            with open(Path(__file__).parent.parent / f"AppData/data/{file_sha256}.json", "r") as f:
                data = load(f)
                if "min_radius" in data.keys() and "max_radius" in data.keys():
                    min_radius, max_radius = data["min_radius"], data["max_radius"]

        # Check if image has been analyzed
        complete_status = "(Not Complete)"
        analyzed_file_hashes_path = Path(__file__).parent.parent / "analyzed_file_hashes.txt"
        with open(analyzed_file_hashes_path, "r") as f:
            analyzed_file_hashes = set(f.read().splitlines())
        if file_sha256 in analyzed_file_hashes:
            complete_status = "(Complete)"

        self.ids.file_name.text = f"{self.parent.file_path.name} {complete_status}"
        self.ids.min_radius.text = str(min_radius)
        self.ids.max_radius.text = str(max_radius)

        base_image = imread(str(self.parent.file_path))
        middle_pixel_map = (int(base_image.shape[1] / 2), int(base_image.shape[0] / 2))
        imwrite(str(Path(__file__).parent.parent / "AppData/meta/base_image.png"), base_image)

        base_image = imread(str(self.parent.file_path))
        image_10 = circle(base_image, middle_pixel_map, 10, (255, 0, 0), 2)
        imwrite(str(Path(__file__).parent.parent / "AppData/meta/current_10.png"), image_10)

        base_image = imread(str(self.parent.file_path))
        image_50 = circle(base_image, middle_pixel_map, 50, (255, 0, 0), 2)
        imwrite(str(Path(__file__).parent.parent / "AppData/meta/current_50.png"), image_50)

        base_image = imread(str(self.parent.file_path))
        image_100 = circle(base_image, middle_pixel_map, 100, (255, 0, 0), 2)
        imwrite(str(Path(__file__).parent.parent / "AppData/meta/current_100.png"), image_100)

        base_image = imread(str(self.parent.file_path))
        image_250 = circle(base_image, middle_pixel_map, 250, (255, 0, 0), 2)
        imwrite(str(Path(__file__).parent.parent / "AppData/meta/current_250.png"), image_250)

        base_image = imread(str(self.parent.file_path))
        image_500 = circle(base_image, middle_pixel_map, 500, (255, 0, 0), 2)
        imwrite(str(Path(__file__).parent.parent / "AppData/meta/current_500.png"), image_500)

        self.ids.base_image.reload()
        self.ids.current_image_10.reload()
        self.ids.current_image_50.reload()
        self.ids.current_image_100.reload()
        self.ids.current_image_250.reload()
        self.ids.current_image_500.reload()

    def release_back(self):
        self.parent.transition.direction = 'right'
        self.parent.current = "file_selector"

    def release_forward(self):
        try:
            self.parent.min_radius = int(self.ids.min_radius.text.strip())
            self.parent.max_radius = int(self.ids.max_radius.text.strip())
        except ValueError:
            self.parent.min_radius, self.parent.max_radius = 0, 0

        self.parent.transition.direction = 'left'
        self.parent.current = "loading_screen"


class MainWindow(Screen, BoxLayout, GridLayout, Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def check_complete_status(self):

        # If all circles have been marked
        circles_left = self.parent.circle_detector.csv_data
        circles_left = circles_left.loc[circles_left['is_circle'] == "unmarked"]
        if len(circles_left) == 0:

            # If image is finished being analyzed

            sha256 = self.parent.circle_detector.csv_data_path.stem
            analyzed_file_hashes_path = Path(__file__).parent.parent / "analyzed_file_hashes.txt"

            is_empty = False
            with open(analyzed_file_hashes_path, "r") as f:
                if not f.read().strip():
                    is_empty = True

            with open(analyzed_file_hashes_path, "a") as f:
                if is_empty:
                    f.write(sha256)
                else:
                    f.write(f"\n{sha256}")

            self.parent.analyzed_file_hashes.add(sha256)

            return "Completed"

        return "Not Complete"

    def remove_complete_status(self):

        file_sha256 = self.parent.circle_detector.csv_data_path.stem
        analyzed_file_hashes_path = Path(__file__).parent.parent / "analyzed_file_hashes.txt"
        if file_sha256 in self.parent.analyzed_file_hashes:
            with open(analyzed_file_hashes_path, "w") as f:
                self.parent.analyzed_file_hashes.remove(file_sha256)
                analyzed_file_hashes = [i + "\n" for i in self.parent.analyzed_file_hashes]

                if analyzed_file_hashes:
                    analyzed_file_hashes[-1] = analyzed_file_hashes[-1].strip()
                    f.writelines(analyzed_file_hashes)

        self.parent.complete_status_str = "Not Complete"

    def enter_main_window(self):

        # Check if image has already been analyzed

        sha256 = self.parent.circle_detector.csv_data_path.stem
        analyzed_file_hashes_path = Path(__file__).parent.parent / "analyzed_file_hashes.txt"
        with open(analyzed_file_hashes_path, "r") as f:
            self.parent.analyzed_file_hashes = set(f.read().splitlines())

        self.parent.complete_status_str = "Not Complete"
        if sha256 in self.parent.analyzed_file_hashes:
            self.parent.complete_status_str = "Completed"

        self.ids.yes_button.state, self.ids.no_button.state = "normal", "normal"

        self.load_images()

    def load_images(self):
        self.ids.current_image.reload()
        self.ids.detected_image.reload()
        self.ids.zoomed_image.reload()

        if self.parent.complete_status_str == "Not Complete":
            self.parent.complete_status_str = self.check_complete_status()

        circles_left = self.parent.circle_detector.num_of_circles
        index = self.parent.circle_detector.index
        self.ids.circle_index.text = f"{index + 1} of {circles_left} " \
                                     f"Detected Circles ({self.parent.complete_status_str})"

    # Bottom Buttons #

    def release_next_unmarked(self):
        yes_button_state, no_button_state = self.parent.circle_detector.next_unmarked(forward=True)
        self.ids.yes_button.state, self.ids.no_button.state = yes_button_state, no_button_state
        self.load_images()

    def release_next(self):
        yes_button_state, no_button_state = self.parent.circle_detector.fetch_next_circle(forward=True)
        self.ids.yes_button.state, self.ids.no_button.state = yes_button_state, no_button_state
        self.load_images()

    def release_prev(self):
        yes_button_state, no_button_state = self.parent.circle_detector.fetch_next_circle(forward=False)
        self.ids.yes_button.state, self.ids.no_button.state = yes_button_state, no_button_state
        self.load_images()

    def release_prev_unmarked(self):
        yes_button_state, no_button_state = self.parent.circle_detector.next_unmarked(forward=False)
        self.ids.yes_button.state, self.ids.no_button.state = yes_button_state, no_button_state
        self.load_images()

    def press_yes(self):
        self.parent.circle_detector.update_choice(choice='yes')
        yes_button_state, no_button_state = self.parent.circle_detector.fetch_next_circle(forward=True)
        self.ids.yes_button.state, self.ids.no_button.state = yes_button_state, no_button_state
        self.load_images()

    def press_no(self):
        self.parent.circle_detector.update_choice(choice='no')
        yes_button_state, no_button_state = self.parent.circle_detector.fetch_next_circle(forward=True)
        self.ids.yes_button.state, self.ids.no_button.state = yes_button_state, no_button_state
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
        self.remove_complete_status()
        self.ids.yes_button.state, self.ids.no_button.state = "normal", "normal"
        self.load_images()

    def press_redo(self):
        self.ids.redo_image.source = str(Path("AppData/icons/pressed.jpeg"))

    def release_redo(self):
        self.ids.redo_image.source = "AppData/icons/redo_default.jpeg"

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
        self.parent.circle_detector = Detector(self.parent.file_path,
                                               self.parent.min_radius, self.parent.max_radius)

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
        anchor_layout.add_widget(Image(source=str(Path(__file__).parent.parent / "AppData/icons/loading.zip"),
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
        self.complete_status_str = None
        self.analyzed_file_hashes = None
        self.analyzed_file_names = None
        self.min_radius = None
        self.max_radius = None

        data_path = Path(__file__).parent.parent / "AppData/data"
        if not exists(data_path):
            mkdir(data_path)

        meta_path = Path(__file__).parent.parent / "AppData/meta"
        if not exists(meta_path):
            mkdir(meta_path)

            # TODO update this to create a new image from memory, will cause issues later
            example_image = Path(__file__).parent.parent / "Example/sun.png"
            copy(example_image, meta_path / "zoomed.png")
            copy(example_image, meta_path / "detected.png")
            copy(example_image, meta_path / "current.png")
            copy(example_image, meta_path / "base_image.png")
            copy(example_image, meta_path / "current_10.png")
            copy(example_image, meta_path / "current_50.png")
            copy(example_image, meta_path / "current_100.png")
            copy(example_image, meta_path / "current_250.png")
            copy(example_image, meta_path / "current_500.png")

    def build(self):
        self.icon = 'AppData/vcu_png.png'
        builder_file = Path(__file__).parent.parent / 'AppData/Dev.kv'
        kv = Builder.load_file(str(builder_file))
        return kv
