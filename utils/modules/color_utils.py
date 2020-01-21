# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
# pylint: disable=C0326

from mathutils import Color


color_channels = {
    'Red':        (1, lambda x: x[0]),
    'Green':      (2, lambda x: x[1]),
    'Blue':       (3, lambda x: x[2]),
    'Hue':        (4, lambda x: Color(x[:3]).h),
    'Saturation': (5, lambda x: Color(x[:3]).s),
    'Value':      (6, lambda x: Color(x[:3]).v),
    'Alpha':      (7, lambda x: x[3]),
    'RGB Average':(8, lambda x: sum(x[:3])/3),
    'Luminosity': (9, lambda x: 0.21*x[0] + 0.72*x[1] + 0.07*x[2]),
    'Color': (10, lambda x: x[:3]),
    'RGBA': (11, lambda x: x[:]),
    }
