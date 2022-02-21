from pathlib import Path
from shutil import rmtree, copytree
from os.path import exists

from kivy.uix.screenmanager import Screen


class DirectoryExporter(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def release_back(self):
        self.parent.transition.direction = 'right'
        self.parent.current = "file_selector"

    def export_all_data(self, root_path):
        dir_path = Path(root_path) / self.ids.dir_path.text

        if exists(dir_path):
            rmtree(dir_path)

        copytree(Path(__file__).parent.parent / "AppData/data", dir_path)
        self.parent.transition.direction = 'right'
        self.parent.current = "file_selector"

    @staticmethod
    def get_home_path():
        return str(Path.home())
