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
from sverchok.utils.context_managers import new_input


nodule_color = (0.899, 0.8052, 0.0, 1.0)


def set_correct_stroke_count(strokes, coords):
    """ ensure that the number of strokes match the sets of coordinates """
    diff = len(strokes) - len(coords)
    if diff < 0:
        # add new strokes
        for _ in range(abs(diff)):
            strokes.new()
    elif diff > 0:
        # remove excess strokes
        for _ in range(diff):
            strokes.remove(strokes[-1])


def pass_data_to_stroke(stroke, coord_set):
    """ adjust the number of points per stroke, to match the incoming coord_set """
    sdiff = len(stroke.points) - len(coord_set)
    if sdiff < 0:
        stroke.points.add(count=abs(sdiff))
    elif sdiff > 0:
        for _ in range(sdiff):
            stroke.points.pop()
    flat_coords = list(itertools.chain.from_iterable(coord_set))
    stroke.points.foreach_set('co', flat_coords)


class SvGreasePencilStrokes(bpy.types.Node, SverchCustomTreeNode):
    ''' Make GreasePencil Strokes '''
    bl_idname = 'SvGreasePencilStrokes'
    bl_label = 'Grease Pencil'
    bl_icon = 'GREASEPENCIL'

    mode_options = [(k, k, '', i) for i, k in enumerate(['3DSPACE', '2DSPACE'])]
    
    draw_mode = bpy.props.EnumProperty(
        items=mode_options, description="Draw Mode",
        default="2DSPACE", update=updateNode
    )

    stroke_color = bpy.props.FloatVectorProperty(
        update=updateNode, name='Stroke', default=(0.958, 1.0, 0.897, 1.0),
        size=4, min=0.0, max=1.0, subtype='COLOR'
    )

    fill_color = bpy.props.FloatVectorProperty(
        update=updateNode, name='Fill', default=(0.2, 0.6, 0.9, 1.0),
        size=4, min=0.0, max=1.0, subtype='COLOR'
    )

    def sv_init(self, context):
        inew = self.inputs.new
        inew('SvObjectSocket', 'frame')
        inew('VerticesSocket', 'coordinates')
        inew('StringsSocket', 'draw cyclic')
        inew('StringsSocket', 'pressure')

        with new_input(self, 'StringsSocket', 'stroke color') as c1:
            c1.prop_name = 'stroke_color'
            c1.nodule_color = nodule_color       

        with new_input(self, 'StringsSocket', 'fill color') as c2:
            c2.prop_name = 'fill_color'
            c2.nodule_color = nodule_color

        onew = self.outputs.new
        onew('SvObjectSocket', 'frame')
        


    def draw_buttons(self, context, layout):
        layout.prop(self, 'draw_mode', expand=True)

    def process(self):
        frame = self.inputs[0]
        coordinates = self.inputs[1]
        if frame.is_linked and coordinates.is_linked:

            strokes = frame.sv_get()
            coords = coordinates.sv_get()
            set_correct_stroke_count(strokes, coords)

            for stroke, coord_set in zip(strokes, coords):
                pass_data_to_stroke(stroke, coord_set)
                stroke.draw_mode = self.draw_mode

                # color.fill_alpha
                # color.alpha


            self.outputs[0].sv_set(strokes)





def register():
    bpy.utils.register_class(SvGreasePencilStrokes)


def unregister():
    bpy.utils.unregister_class(SvGreasePencilStrokes)
