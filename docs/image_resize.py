#!/usr/bin/python3

from PIL import Image, ImageFont, ImageDraw
import os
from pygifsicle import optimize


gWIDTH = 800

def init():
    srcs = os.path.join("_build", "html", "_static", "images")
    for root, dirs, files in os.walk(srcs):
        for file in files:
            check(file)
def check(src):
    if src.endswith('gif'):
        #optimize(src)
        return
    else:
        # ====
        destin = os.path.join("_build", "html", "_static", "images", src)
        img = Image.open(destin)
        width, height = img.size
        # ====
        if width > gWIDTH:
            height = int((gWIDTH/width)*height)
            img_res = img.resize((gWIDTH, height), Image.LANCZOS)
            img_res.save(destin)
            print(f'RESIZED {gWIDTH}x{height} {destin}',end='/r')

if __name__ == '__main__':
    init()
