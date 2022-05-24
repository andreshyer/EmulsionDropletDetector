from threading import Thread
from pathlib import Path

from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.screenmanager import Screen
from kivy.clock import mainthread
from kivy.uix.image import Image

from Core.CircleDectector import Detector


class LoadingScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load_image(self):
        Thread(target=self._load_image).start()

    def _load_image(self):

        self._loading_bar()
        self.parent.circle_detector = Detector(self.parent.file_path,
                                               self.parent.min_radius,
                                               self.parent.max_radius,
                                               self.parent.max_diff_rad,
                                               self.parent.max_dist)

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
