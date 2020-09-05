"""
in pitch_in s n=2 d=0.5
in depth_in s n=2 d=1.0
in height_in s n=2 d=4.0
in radius_in s n=2 d=1.0
out solid_out So
"""

from sverchok.dependencies import FreeCAD

if FreeCAD is None:
    raise Exception("FreeCAD libraries are not available")

from FreeCAD import Base
import Part

solid_out = []
solid = Part.makeThread(pitch_in, depth_in, height_in, radius_in)
solid_out.append(solid)

