# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import xml.etree.ElementTree as ET

def get_xml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    return tree, root

def disect_element(element, parts):
    return [int(element.get(p)) for p in parts.split()]

def get_lookup_dict(fnt_path):
    """
    convert the fnt xml into a usable uv lookup dict

    this:  
       <char id="180" x="16" y="198" width="15" height="32" xoffset="0" yoffset="0" xadvance="15" page="0" chnl="15" />
    becomes:
       180: [
            ((0.0625, 0.7734375), (0.12109375, 0.7734375), (0.12109375, 0.8984375)), 
            ((0.0625, 0.7734375), (0.12109375, 0.8984375), (0.0625, 0.8984375))
       ]

    """
    tree, root = get_xml(r"C:\Users\zeffi\Desktop\GITHUB\sverchok\utils\modules\bitmap_font\consolas.fnt")
    common = root.find("common")
    chars = root.find("chars")
    scale_w = int(common.get('scaleW'))
    scale_h = int(common.get('scaleH'))

    # return two uv triangles for each character
    uv_dict = {}
    for element in list(chars):
        id, x, y, width, height = disect_element(element, "id x y width height")
        
        left = x / scale_w
        right = (x + width) / scale_w
        top = y / scale_h
        bottom = (y + height) / scale_h
        
        A = (left, top)
        B = (right, top)
        C = (right, bottom)
        D = (left, bottom)
        uv_dict[id] = [(A, B, C), (A, C, D)]

    return uv_dict

# uv_dict = get_lookup_dict(r"C:\Users\zeffi\Desktop\GITHUB\sverchok\utils\modules\bitmap_font\consolas.fnt")

def letters_to_uv(letters, fnt):
    """
    expects a 1 or more list of letters, converts to ordinals
    """
    uvs = []
    add_uv = uvs.append
    unrecognized = fnt.get(ord(':')) 

    for letter in letters:
        ordinal = ord(letter)
        details = fnt.get(ordinal, unrecognized)
        add_uv(details[0])
        add_uv(details[1])

    return uvs
