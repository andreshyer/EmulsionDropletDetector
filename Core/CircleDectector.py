from pathlib import Path
from os import listdir
from hashlib import sha256
from json import load, dump

import cv2
from numpy import uint16, around
from pandas import DataFrame, read_csv


class Detector:

    def __init__(self, file_path):
        # Define original image
        self.file_path = Path(file_path)
        self.original_image = cv2.imread(file_path, cv2.IMREAD_COLOR)

        # Transform image into grey scale if not already done
        self.machine_image = cv2.GaussianBlur(self.original_image, (0, 0), cv2.BORDER_DEFAULT)
        self.machine_image = cv2.cvtColor(self.original_image, cv2.COLOR_RGB2GRAY)

        # Grab data in cached csv file. If not cached, create one.
        self.index = None
        self.csv_data = self._parse_stored_data()
        if self.csv_data.empty:
            self._detect_circles()

        # Verify any
        if self.csv_data.empty:
            self.has_circles = False

        if not self.csv_data.empty:
            self.has_circles = True

            # Add on already calculated circles to image
            self.current_image = self.original_image.copy()
            marked_circles = self.csv_data.loc[self.csv_data['is_circle'] == 'yes']
            for index, row in marked_circles.iterrows():
                cv2.circle(self.current_image, (row['x'], row['y']), row['r'], (255, 0, 0), 2)

            # Init first found of pictures
            self.num_of_circles = len(self.csv_data)
            self.detect_next_circle()

    def detect_next_circle(self, forward=True):

        df = self.csv_data.loc[self.csv_data['is_circle'] == 'unmarked']
        if not df.empty:

            # Update the index
            if forward:
                self.index += 1
                if self.index >= self.num_of_circles:
                    self.index = 0
            if not forward:
                self.index -= 1
                if self.index <= -1:
                    self.index = self.num_of_circles - 1

            working_circle = self.csv_data.iloc[[self.index]].to_dict('records')[0]
            x, y, r = working_circle['x'], working_circle['y'], working_circle['r']

            self._get_current_image(x, y, r)
            self._get_detected_image(x, y, r)
            self._get_zoomed_image(x, y, r)

            with open(self.index_pointer_file, 'w') as f:
                dump(self.index, f)

            self._update_status()

    def update_choice(self, choice):

        if choice == 'yes':
            working_circle = self.csv_data.iloc[[self.index]].to_dict('records')[0]
            x, y, r = working_circle['x'], working_circle['y'], working_circle['r']

            self.csv_data.at[self.index, 'is_circle'] = 'yes'
            self._update_current_image(x, y, r, add_circle=True)

        if choice == 'no':
            if self.csv_data.at[self.index, 'is_circle'] == 'yes':
                self.csv_data.at[self.index, 'is_circle'] = 'no'
                self._update_current_image(add_circle=False)
            else:
                self.csv_data.at[self.index, 'is_circle'] = 'no'

        if choice == 'unmarked':
            if self.csv_data.at[self.index, 'is_circle'] == 'yes':
                self.csv_data.at[self.index, 'is_circle'] = 'unmarked'
                self._update_current_image(add_circle=False)
            if self.csv_data.at[self.index, 'is_circle'] == 'no':
                self.csv_data.at[self.index, 'is_circle'] = 'unmarked'

        self.csv_data.to_csv(self.csv_data_path, index=False)
        self._update_status()

    def clear_all_data(self):
        self.csv_data['is_circle'] = 'unmarked'
        self.csv_data.to_csv(self.csv_data_path, index=False)
        self._update_current_image(add_circle=False)
        self.index = -1
        self.detect_next_circle(forward=True)
        self._update_status()

    def _update_status(self):
        if self.csv_data.at[self.index, 'is_circle'] == 'yes':
            self.current_index_is_circle = 'yes'
        elif self.csv_data.at[self.index, 'is_circle'] == 'no':
            self.current_index_is_circle = 'no'
        elif self.csv_data.at[self.index, 'is_circle'] == 'unmarked':
            self.current_index_is_circle = 'unmarked'

    def _parse_stored_data(self):

        with open(self.file_path, "rb") as f:
            file_sha256 = sha256(f.read()).hexdigest()

        self.csv_data_path = Path(__file__).parent.parent / f"AppData/data/{file_sha256}.csv"
        if self.csv_data_path.name in listdir(Path(__file__).parent.parent / "AppData/data"):
            df = read_csv(self.csv_data_path)
        else:
            df = DataFrame(columns=['x', 'y', 'r', 'is_circle'])

        self.index_pointer_file = Path(__file__).parent.parent / f"AppData/data/{file_sha256}.json"
        if self.index_pointer_file.name in listdir(Path(__file__).parent.parent / "AppData/data"):
            with open(self.index_pointer_file, 'r') as f:
                self.index = load(f) - 1
        else:
            self.index = -1

        return df

    def _detect_circles(self):

        circles = cv2.HoughCircles(self.machine_image, cv2.HOUGH_GRADIENT, 1, 20,
                                   param1=90, param2=40, minRadius=0, maxRadius=0)
        if circles is not None:
            circles = uint16(around(circles))
            circle_data = []
            for i in circles[0, :]:
                x, y, r = i[0], i[1], i[2]
                circle_data.append({'x': x, 'y': y, 'r': r, 'is_circle': 'unmarked'})
            self.csv_data = DataFrame(circle_data)
            self.csv_data.to_csv(self.csv_data_path, index=False)

    def _update_current_image(self, x=None, y=None, r=None, add_circle=True):
        if add_circle:
            cv2.circle(self.current_image, (x, y), r, (255, 0, 0), 2)
        else:
            self.current_image = self.original_image.copy()
            marked_circles = self.csv_data.loc[self.csv_data['is_circle'] == 'yes']
            for index, row in marked_circles.iterrows():
                cv2.circle(self.current_image, (row['x'], row['y']), row['r'], (255, 0, 0), 2)

    def _get_current_image(self, x, y, r):
        current_image = cv2.circle(self.current_image.copy(), (x, y), r, (0, 0, 255), 2)
        cv2.imwrite(str(Path(__file__).parent.parent / "AppData/meta/current.png"), current_image)

    def _get_detected_image(self, x, y, r):

        # Draw circle around orginial image and save it
        detected_image = cv2.circle(self.original_image.copy(), (x, y), r, (0, 0, 255), 2)
        cv2.imwrite(str(Path(__file__).parent.parent / "AppData/meta/detected.png"), detected_image)

    def _get_zoomed_image(self, x, y, r):

        # Define coordinates around circle
        max_y = self.original_image.shape[0]
        max_x = self.original_image.shape[1]
        y_top = min(y + r, max_y)
        y_bottom = max(y - r, 0)
        x_right = min(x + r, max_x)
        x_left = max(x - r, 0)

        # Crop then save the image
        zoomed_image = self.original_image[y_bottom:y_top, x_left:x_right]
        cv2.imwrite(str(Path(__file__).parent.parent / "AppData/meta/zoomed.png"), zoomed_image)
