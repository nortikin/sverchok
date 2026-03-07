"""
in filepath FP
out verts v
"""

# more elaborate example is found here  (includes applying transforms)
#
# https://gist.github.com/zeffii/2fdd78613801e5e137874136b1773781
#

import ast
import re
import xml.etree.ElementTree as ET

# input path will probably be wrapped using [[  ]], 
# therefore use [0][0] to extract the path string

file_path = filepath[0][0]
print(file_path)

with open(file_path) as ofile:
    file_string = re.sub("inkscape:", '', ofile.read())
    root = ET.fromstring(file_string)
    
    for item in root.findall("g"):
        for inner_item in item.findall("g"):
            a = inner_item.get("transform")
            print(a)
            for polygon in inner_item.findall("polygon"):
                # print(polygon.get("points"))
                new_verts = ast.literal_eval(polygon.get("points").replace(" ", ","))  # flat
                coords_2d = np.array(new_verts).reshape((-1, 2))                       # 2d vectors
                coords_3d = np.hstack((coords_2d, np.zeros((coords_2d.shape[0], 1))))  # 3d vectors
                verts.append(coords_3d.tolist())  #  tolist is optional if downstream nodes can handle np arrays
