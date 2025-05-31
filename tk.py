import tkinter as tk
import threading
import time

# ===================================================================
#  Конфігурація (можна налаштувати під власні потреби)
# ===================================================================
WINDOW_BG_COLOR = "black"   # Важливо: цей колір буде прозорим
WINDOW_TRANSPARENT_COLOR = WINDOW_BG_COLOR
WINDOW_UPDATE_INTERVAL_MS = 50  # Інтервал оновлення інтерфейсу (мс)

# Розміри і кольори елементів
CROSSHAIR_COLOR = "#FF0000"      # Червоний приціл
CROSSHAIR_THICKNESS = 2
TARGET_RECT_COLOR = "#00FF00"    # Зелена рамка для цілі
TARGET_RECT_THICKNESS = 2

TELEMETRY_TEXT_COLOR = "#FFFFFF"  # Білий текст телеметрії
TELEMETRY_FONT = ("JetBrains Mono Bold", 14)

# Примерні координати та розміри (за замовчуванням — центр екрану)
# Реальні значення будете отримувати динамічно із дрону
DUMMY_ALTITUDE = 120     # метри
DUMMY_SPEED = 15.3       # м/с
DUMMY_DISTANCE = 300     # метри до цілі
DUMMY_TARGET_BOX = ( -50, -50,  50,  50 )  # відносно центру екрана


# ===================================================================
#  Функції–заготовки для отримання даних із дрону
#  (тут просто повертають заглушкові значення)
# ===================================================================
def get_drone_telemetry():
    """
    Повертає кортеж (висота, швидкість, відстань до цілі).
    У вас має бути свій спосіб зв'язку з дроном (наприклад, через сокети
    чи бібліотеку MAVLink), який повертатиме реальні дані.
    """
    # TODO: замініть на реальні виклики до апаратури/сервера
    altitude = DUMMY_ALTITUDE         # метри
    speed = DUMMY_SPEED               # м/с
    distance_to_target = DUMMY_DISTANCE  # метри
    return altitude, speed, distance_to_target

def get_target_box():
    """
    Повертає координати прямокутника-целі у вигляді (x1, y1, x2, y2),
    де (0,0) — центр екрану.
    Ці координати мають бути розраховані, наприклад, з аналізу відео чи
    GPS/датчиків, залежно від логіки вашого «камікадзе»-дрону.
    """
    # TODO: тут має бути реальна обробка
    return DUMMY_TARGET_BOX


# ===================================================================
#  Головний клас GUI
# ===================================================================
class DroneOverlayApp:
    def __init__(self):
        # 1) Створюємо прозоре повноекранне вікно
        self.root = tk.Tk()
        self.root.title("Kamikaze Drone Overlay")
        # Робимо вікно фулскрін і без рамок
        self.root.attributes("-fullscreen", True)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        # Прозорість: будь-який піксель кольору WINDOW_TRANSPARENT_COLOR (black) буде прозорим
        self.root.wm_attributes("-transparentcolor", WINDOW_TRANSPARENT_COLOR)

        # 2) Створюємо Canvas на весь екран
        self.canvas = tk.Canvas(
            self.root,
            bg=WINDOW_BG_COLOR,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # 3) Отримуємо розміри екрану
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        # Центр екрану
        self.cx = self.screen_width // 2
        self.cy = self.screen_height // 2

        # 4) Запускаємо оновлення інтерфейсу у циклі
        self.running = True
        self._start_update_loop()

        # 5) Прив’язуємо клавішу Esc для виходу
        self.root.bind("<Escape>", lambda e: self._shutdown())

    def _start_update_loop(self):
        """
        Запускає фоновий потік, який кожні WINDOW_UPDATE_INTERVAL_MS
        оновлює динамічні елементи на Canvas.
        """
        threading.Thread(target=self._update_loop, daemon=True).start()

    def _update_loop(self):
        while self.running:
            # 1) Очищаємо динамічну групу елементів
            self.canvas.delete("dynamic")

            # 2) Малюємо приціл (статичний — але оновлюємо його одразу)
            self._draw_crosshair()

            # 3) Малюємо рамку для цілі (отримуємо з get_target_box)
            tb = get_target_box()
            self._draw_target_box(tb)

            # 4) Малюємо телеметрію (висота, швидкість, дистанція)
            tel = get_drone_telemetry()
            self._draw_telemetry(tel)

            # 5) Затримка до наступного оновлення
            time.sleep(WINDOW_UPDATE_INTERVAL_MS / 1000.0)

    def _draw_crosshair(self):
        """
        Малюємо приціл у центрі екрана — дві лінії, що перетинаються.
        """
        cx, cy = self.cx, self.cy
        size = 20  # половина довжини ліній прицілу

        # Горизонтальна лінія
        self.canvas.create_line(
            cx - size, cy,
            cx + size, cy,
            fill=CROSSHAIR_COLOR,
            width=CROSSHAIR_THICKNESS,
            tags="dynamic"
        )

        # Вертикальна лінія
        self.canvas.create_line(
            cx, cy - size,
            cx, cy + size,
            fill=CROSSHAIR_COLOR,
            width=CROSSHAIR_THICKNESS,
            tags="dynamic"
        )

    def _draw_target_box(self, tb):
        """
        Малюємо рамку навколо цілі.
        tb = (x1, y1, x2, y2) — відносно центру екрану.
        Переводимо у координати Canvas.
        """
        x1_rel, y1_rel, x2_rel, y2_rel = tb
        x1 = self.cx + x1_rel
        y1 = self.cy + y1_rel
        x2 = self.cx + x2_rel
        y2 = self.cy + y2_rel

        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=TARGET_RECT_COLOR,
            width=TARGET_RECT_THICKNESS,
            tags="dynamic"
        )

    def _draw_telemetry(self, tel):
        """
        Телеметрія: малює текстовий блок у верхній лівій частині екрана.
        tel = (altitude, speed, distance)
        """
        altitude, speed, distance = tel
        lines = [
            f"Altitude: {altitude:.1f} m",
            f"Speed:    {speed:.1f} m/s",
            f"Distance: {distance:.1f} m"
        ]

        x0, y0 = 20, 20  # відступ від лівого-верхнього краю
        for i, line in enumerate(lines):
            self.canvas.create_text(
                x0,
                y0 + i *  20,  # відступ 20px між рядками
                anchor="nw",
                text=line,
                fill=TELEMETRY_TEXT_COLOR,
                font=TELEMETRY_FONT,
                tags="dynamic"
            )

    def _shutdown(self):
        """
        Зупиняємо оновлення та закриваємо вікно.
        Звичайна ESC-обробка.
        """
        self.running = False
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# ===================================================================
#  Запуск програми
# ===================================================================
if __name__ == "__main__":
    app = DroneOverlayApp()
    app.run()
