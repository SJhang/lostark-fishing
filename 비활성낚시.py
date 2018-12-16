import os, sys
import re
import win32gui

import numpy as np
import cv2
from PIL import Image
import ctypes
from ctypes.wintypes import (BOOL, DOUBLE, DWORD, HBITMAP, HDC, HGDIOBJ,  # noqa
                                 HWND, INT, LPARAM, LONG, UINT, WORD)  # noqa

# script_dir = os.path.dirname(__file__)
# rel_path = "./assets/"
# abs_file_path = os.path.join(script_dir, rel_path)       
os.chdir(os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop'))         
SRCCOPY = 13369376
DIB_RGB_COLORS = BI_RGB = 0

class RECT(ctypes.Structure):
    _fields_ = [('left', ctypes.c_long),
                ('top', ctypes.c_long),
                ('right', ctypes.c_long),
                ('bottom', ctypes.c_long)]

class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [('biSize', DWORD), ('biWidth', LONG), ('biHeight', LONG),
                    ('biPlanes', WORD), ('biBitCount', WORD),
                    ('biCompression', DWORD), ('biSizeImage', DWORD),
                    ('biXPelsPerMeter', LONG), ('biYPelsPerMeter', LONG),
                    ('biClrUsed', DWORD), ('biClrImportant', DWORD)]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [('bmiHeader', BITMAPINFOHEADER), ('bmiColors', DWORD * 3)]
    
# Function shorthands
GetClientRect = ctypes.windll.user32.GetClientRect
GetWindowRect = ctypes.windll.user32.GetWindowRect
PrintWindow = ctypes.windll.user32.PrintWindow
GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
IsWindowVisible = ctypes.windll.user32.IsWindowVisible
EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool,
                                        ctypes.POINTER(ctypes.c_int),
                                        ctypes.POINTER(ctypes.c_int))

GetWindowDC = ctypes.windll.user32.GetWindowDC
CreateCompatibleDC = ctypes.windll.gdi32.CreateCompatibleDC
CreateCompatibleBitmap = ctypes.windll.gdi32.CreateCompatibleBitmap
SelectObject = ctypes.windll.gdi32.SelectObject
BitBlt = ctypes.windll.gdi32.BitBlt
DeleteObject = ctypes.windll.gdi32.DeleteObject
GetDIBits = ctypes.windll.gdi32.GetDIBits

EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible

# Arg types
ctypes.windll.user32.GetWindowDC.argtypes = [HWND]
ctypes.windll.gdi32.CreateCompatibleDC.argtypes = [HDC]
ctypes.windll.gdi32.CreateCompatibleBitmap.argtypes = [HDC, INT, INT]
ctypes.windll.gdi32.SelectObject.argtypes = [HDC, HGDIOBJ]
ctypes.windll.gdi32.BitBlt.argtypes = [HDC, INT, INT, INT, INT, HDC, INT, INT, DWORD]
ctypes.windll.gdi32.DeleteObject.argtypes = [HGDIOBJ]
ctypes.windll.gdi32.GetDIBits.argtypes = [HDC, HBITMAP, UINT, UINT, ctypes.c_void_p,
                                    ctypes.POINTER(BITMAPINFO), UINT]
# Return types
ctypes.windll.user32.GetWindowDC.restypes = HDC
ctypes.windll.gdi32.CreateCompatibleDC.restypes = HDC
ctypes.windll.gdi32.CreateCompatibleBitmap.restypes = HBITMAP
ctypes.windll.gdi32.SelectObject.restypes = HGDIOBJ
ctypes.windll.gdi32.BitBlt.restypes = BOOL
ctypes.windll.gdi32.GetDIBits.restypes = INT
ctypes.windll.gdi32.DeleteObject.restypes = BOOL


titles = []
def foreach_window(hwnd, lParam):
    if IsWindowVisible(hwnd):
        length = GetWindowTextLength(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        GetWindowText(hwnd, buff, length + 1)
        titles.append(buff.value)
    return True

EnumWindows(EnumWindowsProc(foreach_window), 0)

def get_lostark_title(titles):
    try:
        r = re.compile(".*LOST ARK")
        filtedTitles = list(filter(r.match, titles))
        if filtedTitles:
            return filtedTitles[0]
        else:
            print('Lost Ark Client not found!')
            return ''

    except Exception as ex:
        print('Error searching hwnd for Lost Ark client from active windows ' + str(ex))
        return -1

LostArkTitle = get_lostark_title(titles)

def get_hwnd(title):
    try:
        hwnd = win32gui.FindWindow(None, title)
        return hwnd
    except Exception as ex:
        print('Error calling win32gui.FindWindow ' + str(ex))
        return -1

hwnd = get_hwnd(LostArkTitle)

def screenshot(hwnd, client=True):
    rect = RECT()
    if client:
        GetClientRect(hwnd, ctypes.byref(rect))
    else:
        GetWindowRect(hwnd, ctypes.byref(rect))
    left, right, top, bottom = rect.left, rect.right, rect.top, rect.bottom
    width, height = right - left, bottom - top

    hwndDC = saveDC = bmp = None
    try:
        hwndDC = GetWindowDC(hwnd)
        saveDC = CreateCompatibleDC(hwndDC)

        bmp = CreateCompatibleBitmap(hwndDC, width, height)
        SelectObject(saveDC, bmp)

        if client:
            PrintWindow(hwnd, saveDC, 1)
        else:
            PrintWindow(hwnd, saveDC, 0)

        buffer_len = height * width * 4
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height  # Why minus? See [1]
        bmi.bmiHeader.biPlanes = 1  # Always 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = BI_RGB
        # Blit
        image = ctypes.create_string_buffer(buffer_len)
        bits = ctypes.windll.gdi32.GetDIBits(saveDC, bmp, 0, height, image, bmi, DIB_RGB_COLORS)
        assert bits == height
        # Replace pixels values: BGRX to RGB
        image2 = ctypes.create_string_buffer(height * width * 3)
        image2[0::3] = image[2::4]
        image2[1::3] = image[1::4]
        image2[2::3] = image[0::4]

        return bytes(image2)

    finally:
        # Clean up
        if hwndDC:
            DeleteObject(hwndDC)
        if saveDC:
            DeleteObject(saveDC)
        if bmp:
            DeleteObject(bmp)

byteImage = screenshot(hwnd)

def imagesearch(image, precision=0.8):
    byteImage = screenshot(hwnd)
    img_array = np.fromstring(byteImage, np.uint8)
    
    print(byteImage, img_array)
    img_np = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    # img_gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    template = cv2.imread(image, 0)

    print(template)
    res = cv2.matchTemplate(byteImage, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if max_val < precision:
        return [-1, -1]
    return max_loc

imagesearch("anteres.png")