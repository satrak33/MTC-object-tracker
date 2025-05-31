import tkinter as tk
import mss
import keyboard
import cv2
import numpy as np
import win32gui
import win32ui
import win32con

# --- Глобальні налаштування та змінні ---
SIZE = 25
GAME_NAME = "Roblox"

SCREEN_CENTER_SCOPE_BBOX = None
GAME_HWND_CACHE = [None]

# Змінні для MOSSE трекера
TRACKER_MOSSE = None
INITIAL_ROI_FOR_TRACKER = None
TRACKER_INITIALIZED_SUCCESSFULLY = False
REINITIALIZE_TRACKER_FLAG = False

def take_window_screenshot(title):
    hwnd = win32gui.FindWindow(None, title)
    if not hwnd:
        return None
    try:
        window_rect = win32gui.GetWindowRect(hwnd)
        window_x, window_y = window_rect[:2]
        client_origin_x, client_origin_y = win32gui.ClientToScreen(hwnd, (0, 0))
        src_x = client_origin_x - window_x
        src_y = client_origin_y - window_y
        left, top, right, bottom = win32gui.GetClientRect(hwnd)
        w, h = right - left, bottom - top
        if w <= 0 or h <= 0:
            print(f"Недійсні розміри вікна '{title}'")
            return None
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
        saveDC.SelectObject(saveBitMap)
        saveDC.BitBlt((0, 0), (w, h), mfcDC, (src_x, src_y), win32con.SRCCOPY)
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        img = np.frombuffer(bmpstr, dtype=np.uint8).reshape(bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        return img
    except Exception as e:
        print(f"Помилка скріншоту: {e}")
        return None

def create_scope(canvas):
    global SCREEN_CENTER_SCOPE_BBOX
    if SCREEN_CENTER_SCOPE_BBOX is None:
        return
    x1, y1, x2, y2 = SCREEN_CENTER_SCOPE_BBOX
    canvas.create_rectangle(x1, y1, x2, y2, outline="#9eed5c", width=2, tags="scope")

def initialize_mosse_tracker():
    global TRACKER_MOSSE, INITIAL_ROI_FOR_TRACKER, TRACKER_INITIALIZED_SUCCESSFULLY
    frame = take_window_screenshot(GAME_NAME)
    if frame is None:
        print("Не вдалося отримати кадр для ініціалізації MOSSE.")
        TRACKER_INITIALIZED_SUCCESSFULLY = False
        return
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    roi_x = max(0, cx - SIZE)
    roi_y = max(0, cy - SIZE)
    roi_w = min(w - roi_x, 2 * SIZE)
    roi_h = min(h - roi_y, 2 * SIZE)
    if roi_w <= 0 or roi_h <= 0:
        print("Недійсний ROI.")
        TRACKER_INITIALIZED_SUCCESSFULLY = False
        return
    INITIAL_ROI_FOR_TRACKER = (roi_x, roi_y, roi_w, roi_h)
    try:
        TRACKER_MOSSE = cv2.legacy.TrackerMOSSE_create()
        TRACKER_MOSSE.init(frame, INITIAL_ROI_FOR_TRACKER)
        TRACKER_INITIALIZED_SUCCESSFULLY = True
        print(f"MOSSE ініціалізовано: {INITIAL_ROI_FOR_TRACKER}")
    except Exception as e:
        print(f"Помилка MOSSE: {e}")
        TRACKER_INITIALIZED_SUCCESSFULLY = False

def track_with_mosse():
    global TRACKER_MOSSE, TRACKER_INITIALIZED_SUCCESSFULLY, REINITIALIZE_TRACKER_FLAG
    if not TRACKER_INITIALIZED_SUCCESSFULLY or TRACKER_MOSSE is None:
        return None
    frame = take_window_screenshot(GAME_NAME)
    if frame is None:
        return None
    try:
        success, bbox = TRACKER_MOSSE.update(frame)
    except Exception as e:
        print(f"Помилка трекінгу MOSSE: {e}")
        REINITIALIZE_TRACKER_FLAG = True
        return None
    if success:
        return bbox
    else:
        print("MOSSE втратив об'єкт.")
        REINITIALIZE_TRACKER_FLAG = True
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
    hwnd = GAME_HWND_CACHE[0]
    try:
        game_x, game_y = win32gui.ClientToScreen(hwnd, (0, 0))
    except win32ui.error:
        GAME_HWND_CACHE[0] = None
        root.after(200, update_canvas, root, canvas)
        return
    if REINITIALIZE_TRACKER_FLAG:
        initialize_mosse_tracker()
        REINITIALIZE_TRACKER_FLAG = False
        if not TRACKER_INITIALIZED_SUCCESSFULLY:
            root.after(1, update_canvas, root, canvas)
            return
    bbox = track_with_mosse()
    if bbox:
        x, y, w, h = map(int, bbox)
        canvas.create_rectangle(game_x + x, game_y + y, game_x + x + w, game_y + y + h,
                                outline="#50edC5", width=2, tags="target")
    root.after(1, update_canvas, root, canvas)

def main():
    global SCREEN_CENTER_SCOPE_BBOX
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
        cx = monitor["left"] + monitor["width"] // 2
        cy = monitor["top"] + monitor["height"] // 2
        SCREEN_CENTER_SCOPE_BBOX = (cx - SIZE, cy - SIZE, cx + SIZE, cy + SIZE)
    except Exception as e:
        print(f"Помилка ініціалізації MSS: {e}")
        SCREEN_CENTER_SCOPE_BBOX = (960 - SIZE, 540 - SIZE, 960 + SIZE, 540 + SIZE)

    root = tk.Tk()
    root.title("MOSSE Tracker OpenCV + Tkinter")
    root.attributes("-fullscreen", True)
    root.overrideredirect(True)
    root.wm_attributes("-topmost", True)
    root.wm_attributes("-transparentcolor", "black")
    canvas = tk.Canvas(root, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    create_scope(canvas)

    keyboard.add_hotkey("q", root.destroy)
    keyboard.add_hotkey("f", initialize_mosse_tracker)

    update_canvas(root, canvas)
    root.mainloop()

if __name__ == "__main__":
    main()
