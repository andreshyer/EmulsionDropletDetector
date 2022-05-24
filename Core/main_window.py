from pathlib import Path

from kivy.uix.widget import Widget
from kivy.uix.screenmanager import Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout


class MainWindow(Screen, BoxLayout, GridLayout, Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def check_complete_status(self, force_remove=False):

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

        else:
            if force_remove:
                self.remove_complete_status()

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

        analyzed_file_hashes_path = Path(__file__).parent.parent / "analyzed_file_hashes.txt"
        with open(analyzed_file_hashes_path, "r") as f:
            self.parent.analyzed_file_hashes = set(f.read().splitlines())

        self.parent.complete_status_str = self.check_complete_status(force_remove=True)

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
        yes_button_state, no_button_state = self.parent.circle_detector.fetch_next_circle(forward=True, yes=True)
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
