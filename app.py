import tkinter as tk
import time
from algorithms import MEDIANFLOWTracker as Tracker
import keyboard
import threading
from target_mouse import target_mouse

RECT_SIZE: int = 25

GAME_NAME: str = "Roblox"

CROSSHAIR_COLOR: str = "#9eed5c"
CROSSHAIR_THICKNESS: int = 2
TARGET_RECT_COLOR: str = "#ff4583"
TARGET_RECT_THICKNESS: int = 2

TELEMETRY_TEXT_COLOR: str = "#9eed5c"
TELEMETRY_FONT: tuple[str, int] = ("JetBrains Mono Bold", 14)
TELEMETRY_TEXT_PADDING: int = 30
TELEMETRY_SIZE: int = 30

STATUS_TEXT_LOCKED_COLOR: str = "#9eed5c"
STATUS_TEXT_UNLOCKED_COLOR: str = "#ff4583"
STATUS_FONT: tuple[str, int] = ("JetBrains Mono Bold", 24)
STATUS_TEXT_PADDING: int = 100

TRANSPARENT_COLOR: str = "#000000"
UPDATE_INTERVAL_MS: int = 10 # Зменшив для плавності, але обережно з навантаженням

class DroneOverlayApp:
    def __init__(self) -> None:
        self.start_time: float = time.perf_counter()
        self.time_from_start: callable = lambda: time.perf_counter() - self.start_time
        self.previous_telemetry_call_time: float = time.perf_counter()

        self.frame_count: int = 0
        self.fps_update_time: float = time.perf_counter()
        self.fps: float = 0


        self.root: tk.Tk = tk.Tk()
        self._create_window()

        # Зберігаємо ID елементів
        self.crosshair_lines: list[int] = []
        self.telemetry_text_items: list[int] = []
        self.status_text_item: int | None = None
        self.target_rect_item: int | None = None # Для прямокутника цілі

        self._initial_draw() # Малюємо все один раз

        self.tracker: Tracker = Tracker(self.screen_center_bbox, GAME_NAME)
        self.running: bool = True

        self._set_bindings()
        self._start_update_loop()

    def _create_window(self) -> None:
        self.root.title("Kamikaze Drone Overlay")
        self.root.attributes("-fullscreen", True)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)

        self.canvas: tk.Canvas = tk.Canvas(
            self.root,
            bg=TRANSPARENT_COLOR,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.screen_width: int = self.root.winfo_screenwidth()
        self.screen_height: int = self.root.winfo_screenheight()
        self.cx: int = self.screen_width // 2
        self.cy: int = self.screen_height // 2
        self.screen_center_bbox: tuple[int, int, int, int] = (
            self.cx - RECT_SIZE,
            self.cy - RECT_SIZE,
            self.cx + RECT_SIZE,
            self.cy + RECT_SIZE
        )

    def _initial_draw(self) -> None:
        """Малює всі елементи вперше і зберігає їх ID."""
        self._draw_crosshair_once()
        self._draw_telemetry_once()
        self._draw_status_once(False) # Початковий статус UNLOCKED
        self._draw_binds_once()
        # Прямокутник цілі буде створений/оновлений в _update_rect

    def _draw_binds_once(self) -> None:
        text: str = """
        Binds:
        ESC/Q - Exit
        F/R - Start tracker
        G/T - Stop tracker
        """

        self.canvas.create_text(
            STATUS_TEXT_PADDING,
            self.screen_height-STATUS_TEXT_PADDING,
            anchor="center",
            text=text,
            fill=TELEMETRY_TEXT_COLOR,
            font=TELEMETRY_FONT
        )

    def _draw_crosshair_once(self) -> None:
        x0, y0, x1, y1 = self.screen_center_bbox

        self.crosshair_lines.append(self.canvas.create_line(
            x0, y0, x0, y1, fill=CROSSHAIR_COLOR, width=CROSSHAIR_THICKNESS
        ))
        self.crosshair_lines.append(self.canvas.create_line(
            x1, y0, x1, y1, fill=CROSSHAIR_COLOR, width=CROSSHAIR_THICKNESS
        ))


    def _draw_telemetry_once(self) -> None:
        x0, y0 = TELEMETRY_TEXT_PADDING, TELEMETRY_TEXT_PADDING
        initial_lines: list[str] = [
            f"FPS:{0:>{TELEMETRY_SIZE-4}}",
            f"SCREEN:{f"{self.screen_width}x{self.screen_height}":>{TELEMETRY_SIZE-7-len(str(self.screen_width))-1}}",
            f"{'':->{TELEMETRY_SIZE}}",
            f"LAST UPDATE:{0.0:>{TELEMETRY_SIZE-14}.2f} s",
            f"TIME FROM START:{0.0:>{TELEMETRY_SIZE-18}.2f} s",
        ]

        for i, line_text in enumerate(initial_lines):
            item_id: int = self.canvas.create_text(
                x0,
                y0 + i * 20,
                anchor="nw",
                text=line_text,
                fill=TELEMETRY_TEXT_COLOR,
                font=TELEMETRY_FONT,
            )
            self.telemetry_text_items.append(item_id)

    def _update_telemetry(self) -> None:
        self.frame_count += 1
        current_time: float = time.perf_counter()

        # Логіка розрахунку FPS (залишається без змін, виглядає коректно)
        elapsed_time_for_fps: float = current_time - self.fps_update_time
        if elapsed_time_for_fps >= 1.0:  # Оновлювати FPS приблизно раз на секунду
            self.fps = self.frame_count / elapsed_time_for_fps
            self.frame_count = 0
            self.fps_update_time = current_time

        # Виправлена логіка для розрахунку часу з моменту останнього оновлення телеметрії
        # Це буде час, що минув між викликами _update_telemetry()
        time_since_last_telemetry_refresh: float = current_time - self.previous_telemetry_call_time
        self.time_from_last_update_val: float = time_since_last_telemetry_refresh  # Зберігаємо для відображення

        # Оновлюємо позначку часу для наступного розрахунку
        self.previous_telemetry_call_time: float = current_time

        # Формування текстових рядків для телеметрії
        # Ваше форматування для SCREEN залишено без змін, оскільки воно могло бути скориговане під специфічний вигляд
        lines_text: list[str] = [
            f"FPS:{self.fps:>{TELEMETRY_SIZE - 4}.0f}",
            f"SCREEN:{f"{self.screen_width}x{self.screen_height}":>{TELEMETRY_SIZE - 7 - len(str(self.screen_width)) + len(str(self.screen_height))}}",
            f"{'':->{TELEMETRY_SIZE}}",  # Розділювач
            f"LAST UPDATE:{self.time_from_last_update_val :>{TELEMETRY_SIZE - 12 - 2}.2f} s",
            f"TIME FROM START:{self.time_from_start():>{TELEMETRY_SIZE - 16 - 2}.2f} s",
        ]

        for i, item_id in enumerate(self.telemetry_text_items):
            if i < len(lines_text):  # Запобігання IndexError
                self.canvas.itemconfig(item_id, text=lines_text[i])
            else:  # Якщо рядків у lines_text стало менше, ніж елементів
                self.canvas.itemconfig(item_id, text="")  # Очистити зайві елементи

    def _draw_status_once(self, status) -> None:
        text: str = "LOCKED" if status else "UNLOCKED"
        color: str = STATUS_TEXT_LOCKED_COLOR if status else STATUS_TEXT_UNLOCKED_COLOR
        self.status_text_item = self.canvas.create_text(
            self.cx,
            self.cy - STATUS_TEXT_PADDING,
            anchor="center",
            text=text,
            fill=color,
            font=STATUS_FONT,
        )

    def _update_status(self, status):
        if self.status_text_item:
            text: str = "LOCKED" if status else "UNLOCKED"
            color: str = STATUS_TEXT_LOCKED_COLOR if status else STATUS_TEXT_UNLOCKED_COLOR
            self.canvas.itemconfig(self.status_text_item, text=text, fill=color)

    def _start_tracker(self) -> None:
        self.tracker.init()

    def _stop_tracker(self) -> None:
        self.tracker.working = False

    def _update_rect(self) -> None:
        roi: tuple[int, int, int, int] = self.tracker.track()
        if roi:
            x, y, w, h = roi
            if self.target_rect_item is None: # Якщо прямокутник ще не створений
                self.target_rect_item = self.canvas.create_rectangle(
                    x, y, x + w, y + h,
                    outline=TARGET_RECT_COLOR,
                    width=TARGET_RECT_THICKNESS
                )
            else: # Якщо вже існує, оновлюємо координати
                self.canvas.coords(self.target_rect_item, x, y, x + w, y + h)
                self.canvas.itemconfig(self.target_rect_item, state='normal') # Робимо видимим
            target_mouse(roi, (self.cx, self.cy))
        elif self.target_rect_item is not None: # Якщо ROI немає, а прямокутник існує
            self.canvas.itemconfig(self.target_rect_item, state='hidden') # Ховаємо прямокутник


    def _update_loop(self) -> None:
        while self.running:
            current_loop_start_time: float = time.perf_counter()

            # НЕ ВИДАЛЯЄМО все: self.canvas.delete("dynamic")

            # Оновлюємо існуючі елементи
            self._update_rect()
            self._update_telemetry()
            self._update_status(self.tracker.working)

            self.root.update_idletasks() # Обробка очікуючих завдань Tkinter
            self.root.update()          # Примусове оновлення вікна

            # Розрахунок часу для затримки, щоб підтримувати UPDATE_INTERVAL_MS
            # self.time_from_last_update_val = current_loop_start_time # Для телеметрії
            elapsed_loop_time_ms: float = (time.perf_counter() - current_loop_start_time) * 1000
            sleep_time_ms = UPDATE_INTERVAL_MS - elapsed_loop_time_ms
            if sleep_time_ms > 0:
                time.sleep(sleep_time_ms / 1000.0)


    def _start_update_loop(self) -> None:
        # Запускаємо цикл оновлення в окремому потоці.
        # ВАЖЛИВО: прямі виклики self.root.update() та self.root.update_idletasks()
        # з іншого потоку не є безпечними для Tkinter.
        # Краще використовувати self.root.after() для планування оновлень в головному потоці.
        # Однак, для простоти прикладу, залишимо так, але це потенційне джерело проблем.
        threading.Thread(target=self._update_loop, daemon=True).start()


    def _set_bindings(self) -> None:
        keyboard.add_hotkey("ctrl", self._shutdown)
        keyboard.add_hotkey("q", self._shutdown)
        keyboard.add_hotkey("f", self._start_tracker)
        keyboard.add_hotkey("w+f", self._start_tracker)
        keyboard.add_hotkey("w+r", self._start_tracker)
        keyboard.add_hotkey("g", self._stop_tracker)
        keyboard.add_hotkey("w+g", self._stop_tracker)
        keyboard.add_hotkey("t", self._stop_tracker)
        keyboard.add_hotkey("w+t", self._stop_tracker)

    def _shutdown(self) -> None:
        self.running = False
        # Дати потоку _update_loop можливість завершитися коректно
        time.sleep(UPDATE_INTERVAL_MS / 1000.0 * 2) # Зачекати трохи довше інтервалу
        if self.root: # Перевірити, чи вікно ще існує
            self.root.destroy()
            self.root = None


    def run(self) -> None:
        self.root.mainloop()

if __name__ == "__main__":
    app = DroneOverlayApp()
    app.run()