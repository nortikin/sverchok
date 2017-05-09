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
from sverchok.data_structure import updateNode, fullList
from sverchok.utils.context_managers import new_input


nodule_color = (0.899, 0.8052, 0.0, 1.0)


def set_correct_stroke_count(strokes, coords):
    """ ensure that the number of strokes match the sets of coordinates """

    diff = len(strokes) - len(coords)
    if diff < 0:
        _ = [strokes.new() for _ in range(abs(diff))]
        strokes.update()
    elif diff > 0:
        _ = [strokes.remove(strokes[-1]) for _ in range(diff)]
        strokes.update()


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


def match_points_and_pressures(pressure_set, num_points):
    num_pressures = len(pressure_set)
    if num_pressures < num_points:
        fullList(pressure_set, num_points)
    elif num_pressures > num_points:
        pressure_set = pressure_set[:num_points]
    return pressure_set


def pass_pressures_to_stroke(stroke, idx, pressures):
    flat_pressures = match_points_and_pressures(pressures[idx], len(stroke.points))

    if len(stroke.points) == len(flat_pressures):
        stroke.points.foreach_set('pressure', flat_pressures)
    else:
        print('not enough pressures for num points')



class SvGreasePencilStrokes(bpy.types.Node, SverchCustomTreeNode):
    ''' Make GreasePencil Strokes '''
    bl_idname = 'SvGreasePencilStrokes'
    bl_label = 'Grease Pencil'
    bl_icon = 'GREASEPENCIL'

    # SCREEN / 3DSPACE / 2DSPACE / 2DIMAGE
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

    draw_cyclic = bpy.props.BoolProperty(default=True, update=updateNode)
    pressure = bpy.props.FloatProperty(default=2.0, min=0.1, max=8.0, update=updateNode)
    num_strokes = bpy.props.IntProperty()

    def sv_init(self, context):
        inew = self.inputs.new
        inew('StringsSocket', 'frame')
        inew('VerticesSocket', 'coordinates')  # per stroke
        inew('StringsSocket', 'draw cyclic').prop_name = 'draw_cyclic'   # per stroke
        inew('StringsSocket', 'pressure').prop_name = 'pressure'         # per point

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


    def get_pressures(self):
        pressures = self.inputs["pressure"].sv_get()
        num_strokes = self.num_strokes

        if len(pressures) == 1:
            if len(pressures[0]) < num_strokes:
                fullList(pressures[0], num_strokes)
            elif len(pressures[0]) > num_strokes:
                pressures[0] = pressures[0][:num_strokes]
            pressures = [[n] for n in pressures[0]]
        else:
            fullList(pressures, num_strokes)

        return pressures


    def process(self):
        frame = self.inputs[0]
        coordinates = self.inputs[1]
        if frame.is_linked and coordinates.is_linked:

            strokes = frame.sv_get()
            coords = coordinates.sv_get()
            self.num_strokes = len(coords)
            set_correct_stroke_count(strokes, coords)

            cyclic_socket_value = self.inputs["draw cyclic"].sv_get()[0]
            fullList(cyclic_socket_value, self.num_strokes)

            pressures = self.get_pressures()
            colors = {}
            colors_fill = {}
            
            for idx, (stroke, coord_set) in enumerate(zip(strokes, coords)):
                try:

                    num_points = len(coord_set)
                    pass_data_to_stroke(stroke, coord_set)

                    stroke.draw_mode = self.draw_mode
                    stroke.draw_cyclic = cyclic_socket_value[idx]
                    stroke.line_width = 3

                    stroke.color.color = self.stroke_color[:3]
                    stroke.color.alpha = self.stroke_color[3]
                    stroke.color.fill_color = self.fill_color[:3]
                    stroke.color.fill_alpha = self.fill_color[3]

                    pass_pressures_to_stroke(stroke, idx, pressures)

                    # ??
                    # strokes.foreach_set('color.color', repeat(stroke_color, len(strokes)))
                    # strokes.foreach_set('color.alpha', repeat(stroke_alpha, len(strokes)))


                except Exception as err:
                    print('iteration=', idx)
                    print(repr(err))




            self.outputs[0].sv_set(strokes)





def register():
    bpy.utils.register_class(SvGreasePencilStrokes)


def unregister():
    bpy.utils.unregister_class(SvGreasePencilStrokes)
