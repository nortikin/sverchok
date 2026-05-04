import bpy
import os

def load_fonts():
    fonts_dir = os.path.dirname(__file__)
    if not os.path.isdir(fonts_dir):
        return
    
    for fname in os.listdir(fonts_dir):
        if fname.lower().endswith((".ttf", ".otf")):
            fpath = os.path.join(fonts_dir, fname)
            # Если шрифт уже есть в bpy.data.fonts, пропускаем
            is_font_loaded_already = [f for f in bpy.data.fonts if f.filepath == fpath]
            if is_font_loaded_already:
                continue
            else:
                try:
                    bpy.data.fonts.load(fpath)
                except:
                    pass
                pass
            pass
        pass
    pass