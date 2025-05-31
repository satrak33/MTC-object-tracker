import tkinter as tk
import mss
import keyboard
import cv2
import numpy as np
import win32gui
import win32ui
import win32con

# --- Глобальні налаштування та змінні ---
SIZE = 25  # Розмір (половина ширини/висоти) для початкового ROI
GAME_NAME = "Roblox"  # Назва ігрового вікна

SCREEN_CENTER_SCOPE_BBOX = None
GAME_HWND_CACHE = [None]  # Кеш для HWND ігрового вікна [hwnd]

# Змінні для CSRT трекера
TRACKER_CSRT = None
INITIAL_ROI_FOR_TRACKER = None  # (x,y,w,h) початковий ROI для трекера
TRACKER_INITIALIZED_SUCCESSFULLY = False
REINITIALIZE_TRACKER_FLAG = False # Новий прапор для реініціалізації

def take_window_screenshot(title):
    hwnd = win32gui.FindWindow(None, title)
    if not hwnd:
        return None

    try:
        window_rect = win32gui.GetWindowRect(hwnd)
        window_x = window_rect[0]
        window_y = window_rect[1]

        client_origin_screen_x, client_origin_screen_y = win32gui.ClientToScreen(hwnd, (0, 0))

        src_x_in_window_dc = client_origin_screen_x - window_x
        src_y_in_window_dc = client_origin_screen_y - window_y

        left_client, top_client, right_client, bot_client = win32gui.GetClientRect(hwnd)
        w_client = right_client - left_client
        h_client = bot_client - top_client

        if w_client <= 0 or h_client <= 0:
            print(f"Вікно '{title}' має недійсні розміри клієнтської області: W={w_client}, H={h_client}")
            return None

        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w_client, h_client)
        saveDC.SelectObject(saveBitMap)

        saveDC.BitBlt((0, 0), (w_client, h_client), mfcDC,
                      (src_x_in_window_dc, src_y_in_window_dc),
                      win32con.SRCCOPY)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        img = np.frombuffer(bmpstr, dtype=np.uint8).reshape(bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # Cleanup resources
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        return img
    except win32ui.error as e:
        # Proper cleanup in case of win32ui error
        print(f"Win32UI Error during screenshot: {e}")
        if 'saveBitMap' in locals() and saveBitMap.GetSafeHandle(): win32gui.DeleteObject(saveBitMap.GetHandle())
        if 'saveDC' in locals() and saveDC.GetSafeHdc(): saveDC.DeleteDC()
        if 'mfcDC' in locals() and mfcDC.GetSafeHdc(): mfcDC.DeleteDC()
        if 'hwndDC' in locals() and hwndDC: win32gui.ReleaseDC(hwnd, hwndDC)
        return None
    except Exception as e:
        print(f"Загальна помилка під час створення скріншоту: {e}")
        return None


def create_scope(canvas):
    global SCREEN_CENTER_SCOPE_BBOX
    if SCREEN_CENTER_SCOPE_BBOX is None:
        return

    x1, y1, x2, y2 = SCREEN_CENTER_SCOPE_BBOX
    canvas.create_rectangle(x1, y1, x2, y2, outline="#9eed5c", width=2, tags="scope")


# Функція для ініціалізації трекера
def initialize_csrt_tracker():
    global TRACKER_CSRT, INITIAL_ROI_FOR_TRACKER, TRACKER_INITIALIZED_SUCCESSFULLY
    frame = take_window_screenshot(GAME_NAME)
    if frame is None:
        print("Не вдалося отримати кадр для ініціалізації трекера CSRT.")
        TRACKER_INITIALIZED_SUCCESSFULLY = False
        return

    h_frame, w_frame = frame.shape[:2]
    center_x_frame = w_frame // 2
    center_y_frame = h_frame // 2

    # Визначаємо початковий ROI (x, y, width, height) відносно центру кадру гри
    roi_x = max(0, center_x_frame - SIZE)
    roi_y = max(0, center_y_frame - SIZE)
    roi_w = min(w_frame - roi_x, 2 * SIZE)  # Ширина ROI
    roi_h = min(h_frame - roi_y, 2 * SIZE)  # Висота ROI

    if roi_w <= 0 or roi_h <= 0:
        print("Недійсний ROI для ініціалізації трекера (можливо, вікно занадто мале або SIZE завеликий).")
        TRACKER_INITIALIZED_SUCCESSFULLY = False
        return

    INITIAL_ROI_FOR_TRACKER = (roi_x, roi_y, roi_w, roi_h)

    try:
        TRACKER_CSRT = cv2.TrackerCSRT_create()
        TRACKER_CSRT.init(frame, INITIAL_ROI_FOR_TRACKER)
        TRACKER_INITIALIZED_SUCCESSFULLY = True
        print(f"Трекер CSRT ініціалізовано. Початковий ROI: {INITIAL_ROI_FOR_TRACKER}")
    except Exception as e:
        print(f"Помилка ініціалізації трекера CSRT: {e}")
        TRACKER_INITIALIZED_SUCCESSFULLY = False


def track_with_csrt():
    global TRACKER_CSRT, TRACKER_INITIALIZED_SUCCESSFULLY, REINITIALIZE_TRACKER_FLAG

    if not TRACKER_INITIALIZED_SUCCESSFULLY or TRACKER_CSRT is None:
        return None  # Повертаємо None, якщо трекер не ініціалізовано

    frame = take_window_screenshot(GAME_NAME)
    if frame is None:
        # print("Не вдалося отримати кадр для відстеження CSRT.")
        return None  # Повертаємо None, якщо кадр не отримано

    try:
        success, bbox = TRACKER_CSRT.update(frame)
    except cv2.error as e:
        print(f"OpenCV Error during tracking update: {e}. Примусова реініціалізація.")
        REINITIALIZE_TRACKER_FLAG = True # Set flag for re-initialization
        return None
    except Exception as e:
        print(f"Загальна помилка під час оновлення трекера: {e}. Примусова реініціалізація.")
        REINITIALIZE_TRACKER_FLAG = True # Set flag for re-initialization
        return None

    if success:
        return bbox
    else:
        print("CSRT втратив об'єкт. Потрібна реініціалізація.")
        REINITIALIZE_TRACKER_FLAG = True # Встановлюємо прапор для реініціалізації
        return None


def update_canvas(root, canvas):
    global GAME_HWND_CACHE, REINITIALIZE_TRACKER_FLAG, TRACKER_INITIALIZED_SUCCESSFULLY
    canvas.delete("target")

    if not GAME_HWND_CACHE[0] or not win32gui.IsWindow(GAME_HWND_CACHE[0]):
        hwnd = win32gui.FindWindow(None, GAME_NAME)
        if not hwnd:
            root.after(200, update_canvas, root, canvas)
            return
        GAME_HWND_CACHE[0] = hwnd

    current_game_hwnd = GAME_HWND_CACHE[0]

    try:
        game_client_tl_x_screen, game_client_tl_y_screen = win32gui.ClientToScreen(current_game_hwnd, (0, 0))
    except win32ui.error:
        GAME_HWND_CACHE[0] = None
        root.after(200, update_canvas, root, canvas)
        return

    # Перевіряємо, чи потрібна реініціалізація трекера
    if REINITIALIZE_TRACKER_FLAG:
        initialize_csrt_tracker()
        REINITIALIZE_TRACKER_FLAG = False # Скидаємо прапор після спроби реініціалізації
        if not TRACKER_INITIALIZED_SUCCESSFULLY: # Якщо реініціалізація не вдалася, пропускаємо відстеження цього кадру
            root.after(1, update_canvas, root, canvas)
            return

    tracked_bbox = track_with_csrt()  # Отримуємо (x_f, y_f, w_f, h_f) або None

    if tracked_bbox is not None:
        x_f, y_f, w_f, h_f = [int(v) for v in tracked_bbox]  # Переконуємось, що координати цілі

        draw_x = game_client_tl_x_screen + x_f
        draw_y = game_client_tl_y_screen + y_f

        canvas.create_rectangle(draw_x, draw_y, draw_x + w_f, draw_y + h_f,
                                 outline="#50edC5", width=2, tags="target")  # Змінив колір для розрізнення

    root.after(1, update_canvas, root, canvas)  # Плануємо наступне оновлення


def main():
    global SCREEN_CENTER_SCOPE_BBOX

    try:
        with mss.mss() as sct:
            # Assuming you have multiple monitors and monitor 1 is your main display.
            # Adjust if your setup is different.
            monitor_details = sct.monitors[1]
        scope_center_x = monitor_details["left"] + monitor_details["width"] // 2
        scope_center_y = monitor_details["top"] + monitor_details["height"] // 2
        SCREEN_CENTER_SCOPE_BBOX = (scope_center_x - SIZE, scope_center_y - SIZE,
                                    scope_center_x + SIZE, scope_center_y + SIZE)
    except Exception as e:
        print(f"Помилка ініціалізації mss або SCREEN_CENTER_SCOPE_BBOX: {e}")
        # Запасний варіант, якщо mss не працює (наприклад, для тестових цілей)
        # Припускаємо стандартний монітор 1920x1080, якщо не вдалося визначити реальні розміри
        SCREEN_CENTER_SCOPE_BBOX = (1920 // 2 - SIZE, 1080 // 2 - SIZE,
                                    1920 // 2 + SIZE, 1080 // 2 + SIZE)

    root = tk.Tk()
    root.title("CSRT Tracker OpenCV + Tkinter")
    root.attributes("-fullscreen", True)
    root.overrideredirect(True)
    root.wm_attributes("-topmost", True)
    root.wm_attributes("-transparentcolor", "black")

    canvas = tk.Canvas(root, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    create_scope(canvas)

    keyboard.add_hotkey("q", root.destroy)
    # 'F' тепер буде ініціалізувати CSRT трекер
    keyboard.add_hotkey("f", initialize_csrt_tracker)

    update_canvas(root, canvas)
    root.mainloop()


if __name__ == "__main__":
    main()