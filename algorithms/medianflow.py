import cv2
from screenshot import take_window_screenshot
from .tracker import Tracker

class MEDIANFLOWTracker(Tracker):
    def __init__(self, bbox: tuple[int, int, int, int], game_name: str) -> None:
        super().__init__(bbox, game_name)

    def init(self) -> None:
        frame = take_window_screenshot(self.game_name)

        x1, y1, x2, y2 = self.bbox
        w = x2 - x1
        h = y2 - y1

        initial_roi_for_tracker = (x1, y1, w, h)
        self.tracker = cv2.legacy.TrackerMedianFlow_create()
        self.tracker.init(frame, initial_roi_for_tracker)

        self.working = True

    def track(self) -> tuple[int, int, int, int] | None:
        if not self.working: return

        frame = take_window_screenshot(self.game_name)
        success, roi = self.tracker.update(frame)

        if success:
            return roi
        else:
            self.working = False
            print("MEDIANFLOW втратив об'єкт.")
            return None
