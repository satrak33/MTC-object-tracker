import tkinter as tk
import mss
import keyboard
import cv2
import numpy as np
import win32gui
import win32ui
import win32con

# --- Глобальні налаштування та змінні ---
SIZE = 25  # Розмір (половина ширини/висоти) для ROI та прицілу
TERM_CRIT = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
ROI_HIST = None
GAME_NAME = "Roblox"  # Назва ігрового вікна

SCREEN_CENTER_SCOPE_BBOX = None

INITIAL_TRACK_WINDOW_FRAME = None  # (x,y,w,h) початкове вікно для CamShift
LAST_TRACKED_WINDOW_FRAME = None  # (x,y,w,h) останнє відоме положення об'єкта

GAME_HWND_CACHE = [None]  # Кеш для HWND ігрового вікна [hwnd]


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

        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        return img
    except win32ui.error:
        if 'saveDC' in locals() and saveDC.GetSafeHdc(): saveDC.DeleteDC()
        if 'mfcDC' in locals() and mfcDC.GetSafeHdc(): mfcDC.DeleteDC()
        if 'hwndDC' in locals() and hwndDC: win32gui.ReleaseDC(hwnd, hwndDC)
        return None
    except Exception:
        return None


def create_scope(canvas):
    global SCREEN_CENTER_SCOPE_BBOX
    if SCREEN_CENTER_SCOPE_BBOX is None:
        print("SCREEN_CENTER_SCOPE_BBOX не ініціалізовано для create_scope")
        return

    x1, y1, x2, y2 = SCREEN_CENTER_SCOPE_BBOX
    canvas.create_rectangle(x1, y1, x2, y2, outline="#9eed5c", width=2, tags="scope")


def set_hist():
    global ROI_HIST, INITIAL_TRACK_WINDOW_FRAME, LAST_TRACKED_WINDOW_FRAME
    frame = take_window_screenshot(GAME_NAME)
    if frame is None:
        print("Не вдалося отримати кадр для встановлення гістограми.")
        return

    h_frame, w_frame = frame.shape[:2]
    center_x_frame = w_frame // 2
    center_y_frame = h_frame // 2

    roi_x1 = max(0, center_x_frame - SIZE)
    roi_y1 = max(0, center_y_frame - SIZE)
    roi_x2 = min(w_frame, center_x_frame + SIZE)
    roi_y2 = min(h_frame, center_y_frame + SIZE)

    if roi_x1 >= roi_x2 or roi_y1 >= roi_y2:
        print("Недійсний ROI для гістограми (можливо, вікно занадто мале або SIZE завеликий).")
        return

    actual_roi_for_slice = frame[roi_y1:roi_y2, roi_x1:roi_x2]
    if actual_roi_for_slice.size == 0:
        print("ROI для гістограми порожній.")
        return

    hsv_roi = cv2.cvtColor(actual_roi_for_slice, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(
        hsv_roi,
        np.array((0., 60., 32.)),
        np.array((180., 255., 255.))
    )
    ROI_HIST = cv2.calcHist([hsv_roi], [0], mask, [180], [0, 180])
    cv2.normalize(ROI_HIST, ROI_HIST, 0, 255, cv2.NORM_MINMAX)

    INITIAL_TRACK_WINDOW_FRAME = (roi_x1, roi_y1, roi_x2 - roi_x1, roi_y2 - roi_y1)
    LAST_TRACKED_WINDOW_FRAME = INITIAL_TRACK_WINDOW_FRAME
    print(f"Гістограму встановлено. Початкове вікно: {INITIAL_TRACK_WINDOW_FRAME}")


def track():
    global ROI_HIST, INITIAL_TRACK_WINDOW_FRAME, LAST_TRACKED_WINDOW_FRAME
    frame = take_window_screenshot(GAME_NAME)

    default_return = LAST_TRACKED_WINDOW_FRAME if LAST_TRACKED_WINDOW_FRAME else (1, 1, 1, 1)

    if frame is None:
        return default_return

    if ROI_HIST is None or INITIAL_TRACK_WINDOW_FRAME is None:
        return default_return

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    dst = cv2.calcBackProject([hsv], [0], ROI_HIST, [0, 180], 1)

    current_search_window = LAST_TRACKED_WINDOW_FRAME

    # Використання CamShift
    # CamShift повертає RotatedRect (ret) та оновлене вікно пошуку (new_window_bounding_box)
    rotated_rect, new_window_bounding_box = cv2.CamShift(dst, current_search_window, TERM_CRIT)

    LAST_TRACKED_WINDOW_FRAME = new_window_bounding_box  # Оновлюємо останнє відоме положення (x,y,w,h)

    # Якщо потрібно було б малювати саме обернений прямокутник:
    # pts = cv2.boxPoints(rotated_rect)
    # pts = np.int0(pts)
    # cv2.polylines(frame,[pts],True, 255,2) # Приклад малювання на самому кадрі гри

    return new_window_bounding_box  # Повертаємо (x,y,w,h) обмежувального прямокутника


def update_canvas(root, canvas):
    global GAME_HWND_CACHE
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

    x_f, y_f, w_f, h_f = track()

    if ROI_HIST is not None and INITIAL_TRACK_WINDOW_FRAME is not None:
        draw_x = game_client_tl_x_screen + x_f
        draw_y = game_client_tl_y_screen + y_f

        canvas.create_rectangle(draw_x, draw_y, draw_x + w_f, draw_y + h_f,
                                outline="#ed5050", width=2, tags="target")

    root.after(30, update_canvas, root, canvas)


def main():
    global SCREEN_CENTER_SCOPE_BBOX

    try:
        with mss.mss() as sct:
            monitor_details = sct.monitors[1]  # [0] - весь екран, [1] - головний монітор
        # Координати для SCREEN_CENTER_SCOPE_BBOX мають бути абсолютними на екрані
        # left, top додаються, якщо монітор не є основним і має зсув
        scope_center_x = monitor_details["left"] + monitor_details["width"] // 2
        scope_center_y = monitor_details["top"] + monitor_details["height"] // 2
        SCREEN_CENTER_SCOPE_BBOX = (scope_center_x - SIZE, scope_center_y - SIZE,
                                    scope_center_x + SIZE, scope_center_y + SIZE)
    except Exception as e:
        print(f"Помилка ініціалізації mss або SCREEN_CENTER_SCOPE_BBOX: {e}")
        print("Встановлення SCREEN_CENTER_SCOPE_BBOX за замовчуванням (може бути неточним)")
        # Запасний варіант, наприклад, для головного монітора, якщо він починається з (0,0)
        # Або якщо у вас один монітор, то monitor_details["left"] і ["top"] будуть 0.
        # Для прикладу, припускаючи центр екрану 1920x1080
        SCREEN_CENTER_SCOPE_BBOX = (1920 // 2 - SIZE, 1080 // 2 - SIZE,
                                    1920 // 2 + SIZE, 1080 // 2 + SIZE)

    root = tk.Tk()
    root.title("Прозоре вікно OpenCV + Tkinter")
    root.attributes("-fullscreen", True)
    root.overrideredirect(True)
    root.wm_attributes("-topmost", True)
    root.wm_attributes("-transparentcolor", "black")

    canvas = tk.Canvas(root, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    create_scope(canvas)

    keyboard.add_hotkey("q", root.destroy)
    keyboard.add_hotkey("f", set_hist)

    update_canvas(root, canvas)
    root.mainloop()


if __name__ == "__main__":
    main()