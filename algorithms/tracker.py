from abc import ABC, abstractmethod
import cv2 # Може знадобитися для типів у майбутньому, або для _get_initial_frame_and_roi
from screenshot import take_window_screenshot # Припускаємо, що модуль існує

class Tracker(ABC):
    def __init__(self, bbox: tuple[int, int, int, int], game_name: str) -> None:
        self.tracker = None  # Загальний атрибут для екземпляра трекера OpenCV.
        self.bbox = bbox  # Зберігаємо початковий bbox (x1, y1, x2, y2)
        self.game_name = game_name
        self.working = False # Початковий стан - трекер не працює

    @abstractmethod
    def init(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def track(self) -> tuple[int, int, int, int] | None:
        raise NotImplementedError