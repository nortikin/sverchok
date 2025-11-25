# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, EnumProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.math import ZERO, FRENET, HOUSEHOLDER, TRACK, DIFF, TRACK_NORMAL, NORMAL_DIR

class SvOffsetCurveNodeMixin:

    modes = [
            ('X', "X (Normal)", "Offset along curve frame's X axis - curve normal in case of Frenet frame", 0),
            ('Y', "Y (Binormal)", "Offset along curve frame's Y axis - curve binormal in case of Frenet frame", 1),
            ('C', "Custom (N / B / T)", "Offset along custom vector in curve frame coordinates - normal, binormal, tangent", 2)
        ]

    algorithms = [
        (FRENET, "Frenet", "Frenet / native rotation. Rotate the profile curve according to Frenet frame of the extrusion curve", 0),
        (ZERO, "Zero-twist", "Zero-twist rotation. Rotate the profile curve according to “zero-twist” frame of the extrusion curve", 1),
        (HOUSEHOLDER, "Householder", "Use Householder reflection matrix", 2),
        (TRACK, "Tracking", "Use quaternion-based tracking. Use the same algorithm as in Blender’s “TrackTo” kinematic constraint. This node currently always uses X as the Up axis", 3),
        (DIFF, "Rotation difference", "Use rotational difference calculation. Calculate rotation as rotation difference between two vectors", 4),
        (TRACK_NORMAL, "Track normal", "Try to maintain constant normal direction by tracking along curve", 5),
        (NORMAL_DIR, "Specified plane", "Offset in plane defined by normal vector in Vector input; i.e., offset in direction perpendicular to Vector input", 6)
    ]

    resolution : IntProperty(
        name = "Resolution",
        description = "The more the number is, the more precise the calculation is, but the slower",
        min = 10, default = 50,
        update = updateNode)

    offset : FloatProperty(
            name = "Offset",
            description = "Offset amount",
            default = 0.1,
            update = updateNode)

