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

from mathutils import Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, StringProperty, BoolProperty

import blf
import bgl

from sverchok.data_structure import updateNode, node_id
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui import nodeview_bgl_viewer_draw_mk2 as nvBGL2

# star imports easing_dict and all easing functions.
from sverchok.utils.sv_easing_functions import *

easing_list = []
for k in sorted(easing_dict.keys()):
    fname = easing_dict[k].__name__
    easing_list.append(tuple([str(k), fname, "", k]))


def simple_grid_xy(func, x, y):

    print('am called')

    def draw_rect(x=0, y=0, w=30, h=10, color=(0.0, 0.0, 0.0, 1.0)):

        bgl.glColor4f(*color)       
        bgl.glBegin(bgl.GL_POLYGON)

        for coord in [(x, y), (x+w, y), (w+x, y-h), (x, y-h)]:
            bgl.glVertex2f(*coord)
        bgl.glEnd()


    # draw bg fill
    draw_rect(x=x, y=y, w=140, h=140, color=(0.0, 0.0, 0.5, 0.5))

    # draw grid
    # ...
    # draw graph-line
    # bgl.glColor3f(*color)



class SvEasingNode(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvEasingNode'
    bl_label = 'Easing 0..1'

    n_id = StringProperty(default='')
    activate = BoolProperty(
        name='Show', description='Activate drawing',
        default=True,
        update=updateNode)

    selected_mode = EnumProperty(
        items=easing_list,
        description="offers easing choice",
        default="0",
        update=updateNode
    )

    in_float = FloatProperty(
        min=0.0, max=1.0, default=0.0, name='Float Input',
        description='input to the easy function', update=updateNode
    )

    def draw_buttons(self, context, l):
        c = l.column()
        c.label(text="set easing function")
        c.prop(self, "selected_mode", text="")
        c.prop(self, 'activate')

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Float").prop_name = 'in_float'
        self.outputs.new('StringsSocket', "Float")

    def process(self):
        p = self.inputs['Float'].sv_get()
        n_id = node_id(self)

        # end early
        nvBGL2.callback_disable(n_id)

        float_out = self.outputs['Float']
        easing_func = easing_dict.get(int(self.selected_mode))
        if float_out.is_linked:
            out = []
            for obj in p:
                r = []
                for i in obj:
                    r.append(easing_func(i))
                out.append(r)
            float_out.sv_set(out)
        else:
            float_out.sv_set([[None]])

        if self.activate:
            x, y = [int(j) for j in (self.location + Vector((self.width + 20, 0)))[:]]
            
            draw_data = {
                'tree_name': self.id_data.name[:],
                'mode': 'custom_function', 
                'custom_function': simple_grid_xy,
                'easing_func': easing_func,
                'loc': (x, y)
            }
            nvBGL2.callback_enable(n_id, draw_data)

        

    # reset n_id on copy
    def copy(self, node):
        self.n_id = ''


def register():
    bpy.utils.register_class(SvEasingNode)


def unregister():
    bpy.utils.unregister_class(SvEasingNode)
