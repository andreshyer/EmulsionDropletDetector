from pathlib import Path
from os import mkdir
from os.path import exists

from cv2 import imwrite
from numpy import zeros
from pandas import read_csv
from kivy import require
from kivy.app import App
from kivy.lang.builder import Builder
from kivy.uix.screenmanager import ScreenManager

# Define that Kivy 2.0.0 is required for code to try and run
require('2.0.0')


class WindowManager(ScreenManager):
    pass


class EmulsionBubbleDetectorApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Declare variable to vary latter
        self.circle_detector = None
        self.file_path = None
        self.complete_status_str = None
        self.analyzed_file_hashes = None
        self.analyzed_file_names = None
        self.min_radius = None
        self.max_radius = None
        self.max_diff_rad = None
        self.max_dist = None

        # Make sure data and meta-data directories exist, if not make them
        data_path = Path(__file__).parent.parent / "AppData/data"
        if not exists(data_path):
            mkdir(data_path)

        # Place blank images for all needed images
        # Kivy requires an image exists if called at some point,
        # which can be updated later.
        meta_path = Path(__file__).parent.parent / "AppData/meta"
        if not exists(meta_path):
            mkdir(meta_path)

            # Create blank images
            base_image = zeros((255, 255))
            dummy_images = [
                "zoomed.png",
                "detected.png",
                "current.png",
                "base_image.png",
                "current_10.png",
                "current_50.png",
                "current_100.png",
                "current_250.png",
                "current_500.png"
            ]
            for dummy_image in dummy_images:
                imwrite(str(meta_path / dummy_image), base_image)

        # Gather which files have been fully analyzed, fix broken hash file
        file_hashes = []
        for file in data_path.iterdir():
            if file.suffix == ".csv":
                df = read_csv(file)
                df = df.loc[df["is_circle"] == "unmarked"]
                if df.empty:
                    file_hashes.append(file.stem)

        # Re-build analyzed_file_hashes.txt with updated data
        analyzed_file_hashes_path = Path(__file__).parent.parent / "analyzed_file_hashes.txt"
        with open(analyzed_file_hashes_path, "w") as f:
            for file_hash in file_hashes:
                f.write(f"{file_hash}\n")

    def build(self):
        builder_file = Path(__file__).parent.parent / f'AppData/kv_files/window_manager.kv'
        kv = Builder.load_file(str(builder_file))
        return kv
