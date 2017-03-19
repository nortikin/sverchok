# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import itertools
import bpy
# import mathutils
# from mathutils import Vector
# from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

class SvGreasePencilStrokes(bpy.types.Node, SverchCustomTreeNode):
    ''' Make GreasePencil Strokes '''
    bl_idname = 'SvGreasePencilStrokes'
    bl_label = 'Grease Pencil'
    bl_icon = 'GREASEPENCIL'

    def sv_init(self, context):
        self.inputs.new('StringsSocket', 'frame')
        self.inputs.new('VerticesSocket', 'coordinates')

    # def draw_buttons(self, context, layout):
    #     ...

    def process(self):
        frame = self.inputs[0]
        coordinates = self.inputs[1]
        if frame.is_linked and coordinates.is_linked:
            # for each set of coordinates make a set of stroke data
            # if more pushed than exist, make more, if fewer are pushed than
            # exist, then remove.
            # use foreach_set..when possible.
            strokes = frame.sv_get()
            coords = coordinates.sv_get()
            # fix length (todo)

            diff = len(strokes) - len(coords)
            if diff < 0:
                # add new strokes
                for _ in range(abs(diff)):
                    strokes.new()
            elif diff > 0:
                # remove excess strokes
                for _ in range(diff):
                    strokes.remove(strokes[-1])

            # will need to introspect, to refresh the content of strokes maybe?
            for stroke, coord_set in zip(strokes, coords):
                sdiff = len(stroke.points) - len(coord_set)
                if sdiff < 0:
                    stroke.points.add(count=abs(sdiff))
                elif sdiff > 0:
                    for _ in range(sdiff):
                        stroke.points.pop()
                flat_coords = list(itertools.chain.from_iterable(coord_set))
                stroke.points.foreach_set('co', flat_coords)






def register():
    bpy.utils.register_class(SvGreasePencilStrokes)


def unregister():
    bpy.utils.unregister_class(SvGreasePencilStrokes)
