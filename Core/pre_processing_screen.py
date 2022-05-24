from pathlib import Path
from hashlib import sha256
from json import load
from os.path import exists

from numpy import nan
from cv2 import imread, imwrite, circle
from kivy.uix.screenmanager import Screen


class PreProcessingScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_current_image(self):

        # Get file hash
        with open(self.parent.file_path, "rb") as f:
            file_sha256 = sha256(f.read()).hexdigest()

        # If json data exists for file, grab min and max radii
        min_radius, max_radius, max_diff_rad, max_dist = 0, 0, 0.05, 0.50
        data_folder_path = Path(__file__).parent.parent / "AppData/data"
        opened_files = list(set([file.stem for file in data_folder_path.iterdir()]))
        if file_sha256 in opened_files:
            with open(Path(__file__).parent.parent / f"AppData/data/{file_sha256}.json", "r") as f:
                data = load(f)
                if "min_radius" in data.keys():
                    min_radius = data['min_radius']

                if "max_radius" in data.keys():
                    max_radius = data['max_radius']

                if "max_diff_rad" in data.keys():
                    max_diff_rad = data["max_diff_rad"]

                if "max_dist" in data.keys():
                    max_dist = data["max_dist"]

        # Check if image has been analyzed
        complete_status = "(Not Complete)"
        analyzed_file_hashes_path = Path(__file__).parent.parent / "analyzed_file_hashes.txt"
        if not exists(analyzed_file_hashes_path):
            with open(analyzed_file_hashes_path, "w") as _:
                pass
        with open(analyzed_file_hashes_path, "r") as f:
            analyzed_file_hashes = set(f.read().splitlines())
        if file_sha256 in analyzed_file_hashes:
            complete_status = "(Complete)"

        self.ids.file_name.text = f"{self.parent.file_path.name} {complete_status}"
        self.ids.min_radius.text = str(min_radius)
        self.ids.max_radius.text = str(max_radius)
        self.ids.max_diff_rad.text = str(max_diff_rad)
        self.ids.max_dist.text = str(max_dist)

        # Gather information from original image
        base_image = imread(str(self.parent.file_path))
        middle_pixel_map = (int(base_image.shape[1] / 2), int(base_image.shape[0] / 2))
        imwrite(str(Path(__file__).parent.parent / "AppData/meta/base_image.png"), base_image)

        # Create images with circles in them
        circle_sizes = [10, 50, 100, 250, 500]
        for circle_size in circle_sizes:
            base_image = imread(str(self.parent.file_path))
            edited_image = circle(base_image, middle_pixel_map, circle_size, (255, 0, 0), 2)
            imwrite(str(Path(__file__).parent.parent / f"AppData/meta/current_{circle_size}.png"),
                    edited_image)

        # Update images in the application
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
        self.parent.min_radius = int(self.ids.min_radius.text.strip())
        self.parent.max_radius = int(self.ids.max_radius.text.strip())
        self.parent.max_diff_rad = float(self.ids.max_diff_rad.text.strip())
        self.parent.max_dist = float(self.ids.max_dist.text.strip())

        self.parent.transition.direction = 'left'
        self.parent.current = "loading_screen"
