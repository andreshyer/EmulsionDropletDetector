from pathlib import Path
from shutil import rmtree
from os import mkdir

from cv2 import imread
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock


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

    def export_all_data(self):
        self.parent.transition.direction = 'left'
        self.parent.current = "directory_exporter"
