from pathlib import Path

from kivy.uix.screenmanager import Screen


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

    @staticmethod
    def get_home_path():
        return str(Path.home())
