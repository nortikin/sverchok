# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from sverchok.settings import get_params

# pylint: disable=c0111
# pylint: disable=c0103

def get_preferences():
    # supplied with default, forces at least one value :)
    props = get_params({
        'render_scale': 1.0,
        'render_location_xy_multiplier': 1.0})
    return props.render_scale, props.render_location_xy_multiplier

class SvNodeViewDrawMixin():

    @property
    def xy_offset(self):
        a = self.location[:]
        b = int(self.width) + 20
        return int(a[0] + b), int(a[1])

    @staticmethod
    def adjust_position_and_dimensions(x, y, width, height):
        scale, multiplier = get_preferences()
        x, y = [x * multiplier, y * multiplier]
        width, height = [width * scale, height * scale]
        return x, y, width, height
