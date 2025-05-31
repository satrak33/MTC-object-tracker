import cv2
from screenshot import take_window_screenshot


class MOSSETracker:
    def __init__(self, bbox, game_name):
        self.tracker_mosse = None
        self.bbox = bbox
        self.game_name = game_name
        self.working = False

    def initialize_mosse_tracker(self):
        frame = take_window_screenshot(self.game_name)
        if frame is None:
            print("Не вдалося отримати кадр для ініціалізації MOSSE.")
            return

        x1, y1, x2, y2 = self.bbox
        w = x2 - x1
        h = y2 - y1

        initial_roi_for_tracker = (x1, y1, w, h)
        self.tracker_mosse = cv2.legacy.TrackerMOSSE_create()
        self.tracker_mosse.init(frame, initial_roi_for_tracker)

        self.working = True

    def track_with_mosse(self):
        if not self.working: return

        frame = take_window_screenshot(self.game_name)
        success, roi = self.tracker_mosse.update(frame)
        if success:
            return roi
        else:
            self.working = False
            print("MOSSE втратив об'єкт.")
            return None
