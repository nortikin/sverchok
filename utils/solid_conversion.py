# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from sverchok.data_structure import map_recursive
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.surface.core import SvSurface
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:

    import Part
    from sverchok.utils.curve.freecad import curve_to_freecad
    from sverchok.utils.surface.freecad import surface_to_freecad, is_solid_face_surface

def to_solid(ob):
    if isinstance(ob, Part.Shape):
        return ob
    elif isinstance(ob, SvCurve):
        return [c.curve.toShape() for c in curve_to_freecad(ob)]
    elif isinstance(ob, SvSurface):
        if is_solid_face_surface(ob):
            return ob.face
        else:
            return surface_to_freecad(ob, make_face=True).face
    else:
        raise TypeError(f"Unknown data type in input: {ob}")

def to_solid_recursive(data):
    return map_recursive(to_solid, data, data_types=(SvCurve, SvSurface, Part.Shape))

