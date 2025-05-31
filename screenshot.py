import win32gui
import win32ui
import win32con
import cv2
import numpy as np

def take_window_screenshot(title):
    hwnd = win32gui.FindWindow(None, title)
    window_rect = win32gui.GetWindowRect(hwnd)
    window_x, window_y = window_rect[:2]
    client_origin_x, client_origin_y = win32gui.ClientToScreen(hwnd, (0, 0))
    src_x = client_origin_x - window_x
    src_y = client_origin_y - window_y
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    w, h = right - left, bottom - top
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