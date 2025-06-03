import win32gui
import win32ui
import win32con
import numpy as np


def take_window_screenshot(title):
    hwnd = win32gui.FindWindow(None, title)
    # Get window and client coordinates only once
    wx, wy, _, _ = win32gui.GetWindowRect(hwnd)
    cx, cy = win32gui.ClientToScreen(hwnd, (0, 0))
    src_x, src_y = cx - wx, cy - wy

    # More direct client rect calculation
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    w, h = right - left, bottom - top

    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
    saveDC.SelectObject(saveBitMap)
    saveDC.BitBlt((0, 0), (w, h), mfcDC, (src_x, src_y), win32con.SRCCOPY)

    # Avoid multiple calls to GetInfo
    bmpinfo = saveBitMap.GetInfo()
    bmp_height = bmpinfo["bmHeight"]
    bmp_width = bmpinfo["bmWidth"]
    # Direct reshape and use only first 3 channels (BGRA→BGR), avoids cv2.cvtColor
    img = np.frombuffer(saveBitMap.GetBitmapBits(True), dtype=np.uint8).reshape(
        bmp_height, bmp_width, 4
    )
    img = img[:, :, :3]

    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)
    return img
