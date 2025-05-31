import tkinter as tk
import time
from mosse import MOSSETracker
import keyboard
import threading


RECT_SIZE = 25

GAME_NAME = "Roblox"

CROSSHAIR_COLOR = "#9eed5c"
CROSSHAIR_THICKNESS = 2
TARGET_RECT_COLOR = "#ff4583"
TARGET_RECT_THICKNESS = 2

TELEMETRY_TEXT_COLOR = "#9eed5c"
TELEMETRY_FONT = ("JetBrains Mono Bold", 14)
TELEMETRY_TEXT_PADDING = 30
TELEMETRY_SIZE = 30

STATUS_TEXT_LOCKED_COLOR = "#9eed5c"
STATUS_TEXT_UNLOCKED_COLOR = "#ff4583"
STATUS_FONT = ("JetBrains Mono Bold", 24)
STATUS_TEXT_PADDING = 100

TRANSPARENT_COLOR = "#000000"
UPDATE_INTERVAL_MS = 10

class DroneOverlayApp:
    def __init__(self):
        self.start_time = time.perf_counter()
        self.time_from_start = lambda: time.perf_counter() - self.start_time

        self.time_from_last_update = time.perf_counter()
        self.fps = 0


        self.root = tk.Tk()
        self._create_window()
        self._draw_crosshair()
        self._draw_telemetry()
        self._draw_status(False)

        self.tracker = MOSSETracker(self.screen_center_bbox, GAME_NAME)
        self.running = True

        self._set_bindings()
        self._start_update_loop()

    def _create_window(self):
        self.root.title("Kamikaze Drone Overlay")
        self.root.attributes("-fullscreen", True)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)

        # 2) Створюємо Canvas на весь екран
        self.canvas = tk.Canvas(
            self.root,
            bg=TRANSPARENT_COLOR,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # 3) Отримуємо розміри екрану
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        # Центр екрану
        self.cx = self.screen_width // 2
        self.cy = self.screen_height // 2
        self.screen_center_bbox = (
            self.cx - RECT_SIZE,
            self.cy - RECT_SIZE,
            self.cx + RECT_SIZE,
            self.cy + RECT_SIZE
        )

    def _start_update_loop(self):
        threading.Thread(target=self._update_loop, daemon=True).start()

    def _draw_crosshair(self):
        """
        Малюємо приціл у центрі екрана — дві лінії, що перетинаються.
        """
        x0, y0, x1, y1 = self.screen_center_bbox

        self.canvas.create_line(
            x0, y0, x0, y1, fill=CROSSHAIR_COLOR, width=CROSSHAIR_THICKNESS, tags="dynamic"
        )

        self.canvas.create_line(
            x1, y0, x1, y1, fill=CROSSHAIR_COLOR, width=CROSSHAIR_THICKNESS, tags="dynamic"
        )


    def _draw_telemetry(self):
        fps = self.fps
        screen = f"{self.screen_width}x{self.screen_height}"
        time_from_last_update = self.time_from_last_update
        time_from_start = self.time_from_start
        lines = [
            f"FPS:{fps:>{TELEMETRY_SIZE-4}}",
            f"SCREEN:{screen:>{TELEMETRY_SIZE-7}}",
            f"{'':->{TELEMETRY_SIZE}}",
            f"LAST UPDATE:{time_from_last_update:>{TELEMETRY_SIZE-14}.2f} s",
            f"TIME FROM START:{time_from_start():>{TELEMETRY_SIZE-18}.2f} s",
        ]

        x0, y0 = TELEMETRY_TEXT_PADDING, TELEMETRY_TEXT_PADDING  # відступ від лівого-верхнього краю
        for i, line in enumerate(lines):
            self.canvas.create_text(
                x0,
                y0 + i *  20,  # відступ 20px між рядками
                anchor="nw",
                text=line,
                fill=TELEMETRY_TEXT_COLOR,
                font=TELEMETRY_FONT,
                tags="dynamic",
                )

    def _draw_status(self, status):
        text = "LOCKED" if status else "UNLOCKED"
        color = STATUS_TEXT_LOCKED_COLOR if status else STATUS_TEXT_UNLOCKED_COLOR
        self.canvas.create_text(
            self.cx,
            self.cy-STATUS_TEXT_PADDING,
            anchor="center",
            text=text,
            fill=color,
            font=STATUS_FONT,
            tags="dynamic"
        )

    def _start_tracker(self):
        self.tracker.initialize_mosse_tracker()

    def _stop_tracker(self):
        self.tracker.working = False

    def _draw_rect(self):
        roi = self.tracker.track_with_mosse()
        if not roi: return

        x, y, w, h = roi

        self.canvas.create_rectangle(
            x,
            y,
            x + w,
            y + h,
            outline=TARGET_RECT_COLOR,
            width=TARGET_RECT_THICKNESS,
            tags="dynamic"
        )

    def _update_loop(self):
        while self.running:
            # 1) Очищаємо динамічну групу елементів
            self.canvas.delete("dynamic")

            # 2) Малюємо приціл (статичний — але оновлюємо його одразу)
            self._draw_crosshair()

            self._draw_rect()

            # 3) Малюємо телеметрію (висота, швидкість, дистанція)
            self._draw_telemetry()

            # 4) Малюємо статус (LOCKED/UNLOCKED)
            status = self.tracker.working
            self._draw_status(status)

            # 5) Затримка до наступного оновлення
            time.sleep(UPDATE_INTERVAL_MS / 1000.0)

    def _set_bindings(self):
        keyboard.add_hotkey("esc", self._shutdown)
        keyboard.add_hotkey("q", self._shutdown)

        keyboard.add_hotkey("f", self._start_tracker)
        keyboard.add_hotkey("r", self._start_tracker)

        keyboard.add_hotkey("g", self._stop_tracker)
        keyboard.add_hotkey("t", self._stop_tracker)


    def _shutdown(self):
        self.running = False
        self.root.destroy()

    def run(self):
        self.root.mainloop()



if __name__ == "__main__":
    app = DroneOverlayApp()
    app.run()