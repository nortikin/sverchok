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

import random

import bpy
import bmesh
import mathutils
from mathutils import Vector, Matrix
from bpy.props import BoolProperty, FloatVectorProperty, StringProperty, EnumProperty, FloatProperty

from node_tree import SverchCustomTreeNode, MatrixSocket
from data_structure import dataCorrect, updateNode, SvGetSocketAnyType, fullList


def get_random_init():
    greek_alphabet = [
        'Alpha', 'Beta', 'Gamma', 'Delta',
        'Epsilon', 'Zeta', 'Eta', 'Theta',
        'Iota', 'Kappa', 'Lamda', 'Mu',
        'Nu', 'Xi', 'Omicron', 'Pi',
        'Rho', 'Sigma', 'Tau', 'Upsilon',
        'Phi', 'Chi', 'Psi', 'Omega']
    return random.choice(greek_alphabet)


class SvMetaballNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    each metaball has 3 main variables:
    - location, radius and sign (Bool, but accepts 0 or 1)
    '''

    bl_idname = 'SvMetaballNode'
    bl_label = 'Sv Metaball Node'
    bl_icon = 'OUTLINER_OB_EMPTY'

    activate = BoolProperty(
        default=True,
        name='ActiveUpdates', description='Activate node?',
        update=updateNode)

    metaball_name = StringProperty(
        default='Alpha',
        description='stores the mesh name found in the object, this mesh is instanced',
        update=updateNode)

    resolution = FloatProperty(default=0.16, min=0.15, update=updateNode)
    render_resolution = FloatProperty(default=0.16, update=updateNode)

    def init(self, context):
        self.inputs.new('VerticesSocket', 'location', 'location')
        self.inputs.new('StringsSocket', 'radius', 'radius')
        self.inputs.new('StringsSocket', 'sign', 'sign')

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "activate", text="Update")

        layout.label("Metaball Obj name", icon='OUTLINER_OB_MESH')
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "metaball_name", text="")

    def draw_buttons_ext(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "resolution", text="view resolution")
        row.prop(self, "render_resolution", text="render resolution")

    def abort_processing(self):
        try:
            l = bpy.data.node_groups[self.id_data.name]
        except Exception as e:
            print(self.name, "cannot run during startup, press update.")
            return True

    def update(self):
        if self.abort_processing() and not self.activate:
            return

        inputs = self.inputs
        if not 'sign' in inputs:
            return

        self.process()

    def metaget(self, s_name, fallback, level):
        '''
        private function for the processing function, accepts level 0..2
        '''
        inputs = self.inputs
        if inputs[s_name].links:
            socket_in = SvGetSocketAnyType(self, inputs[s_name])
            if level == 1:
                data = dataCorrect(socket_in)[0]
            elif level == 2:
                data = dataCorrect(socket_in)[0][0]
            else:
                data = dataCorrect(socket_in)
            return data
        else:
            return fallback

    def get_metaball_reference(self):
        scene = bpy.context.scene
        objs = bpy.data.objects
        metaballs = bpy.data.metaballs

        # add metaball object
        if not (self.metaball_name in metaballs):
            mball = metaballs.new(self.metaball_name)
            obj = objs.new(self.metaball_name+"OBJ", mball)
            scene.objects.link(obj)
        else:
            mball = metaballs[self.metaball_name]
        return mball

    def process(self):
        locations = self.metaget('location', [(0, 0, 0)], level=1)
        signs = self.metaget('sign', [0], level=2)
        radii = self.metaget('radius', [0.5], level=2)

        fullList(signs, len(locations))
        fullList(radii, len(locations))

        mball = self.get_metaball_reference()
        mball.render_resolution = self.render_resolution
        mball.resolution = self.resolution  # View resolution

        # print('-- mball elements', len(mball.elements))
        for idx, (co, sign, radius) in enumerate(zip(locations, signs, radii)):
            # print(idx, co, sign, radius)
            if idx > len(mball.elements)-1:
                ele = mball.elements.new()
            else:
                ele = mball.elements[idx]
            # print(sign, radius)
            ele.co = co
            ele.use_negative = sign
            ele.radius = radius

        # remove dead metaballs
        n = len(mball.elements) - idx
        if n > 0:
            for i in range(n):
                mball.elements.remove(mball.elements[-1])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvMetaballNode)


def unregister():
    bpy.utils.unregister_class(SvMetaballNode)
