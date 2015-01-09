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

from math import sin, cos, pi, degrees, radians
import random

import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (fullList, match_long_repeat, updateNode,
                            SvSetSocketAnyType, SvGetSocketAnyType)

def rotate(l, y=1):
   if len(l) == 0:
      return l
   y = y % len(l)
   return list(l[y:]) + list(l[:y])

class SvNGonNode(bpy.types.Node, SverchCustomTreeNode):
    ''' NGon '''
    bl_idname = 'SvNGonNode'
    bl_label = 'NGon'
    bl_icon = 'OUTLINER_OB_EMPTY'

    rad_ = FloatProperty(name='Radius', description='Radius',
                         default=1.0,
                         update=updateNode)
    sides_ = IntProperty(name='N Sides', description='Number of polygon sides',
                        default=5, min=3,
                        update=updateNode)
    rand_seed_ = FloatProperty(name='Seed', description='Random seed',
                        default=0.0,
                        update=updateNode)
    rand_r_ = FloatProperty(name='RandomR', description='Radius randomization amplitude',
                        default=0.0, min=0.0,
                        update=updateNode)
    rand_phi_ = FloatProperty(name='RandomPhi', description='Angle randomization amplitude (radians)',
                        default=0.0, min=0.0, max=pi,
                        update=updateNode)
    shift_ = IntProperty(name='Shift', description='Edges bind shift (star factor)',
                        default=0, min=0,
                        update=updateNode)
                        

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Radius").prop_name = 'rad_'
        self.inputs.new('StringsSocket', "N Sides").prop_name = 'sides_'
        self.inputs.new('StringsSocket', "RandomR").prop_name = 'rand_r_'
        self.inputs.new('StringsSocket', "RandomPhi").prop_name = 'rand_phi_'
        self.inputs.new('StringsSocket', "RandomSeed").prop_name = 'rand_seed_'
        self.inputs.new('StringsSocket', "Shift").prop_name = 'shift_'

        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polygons", "Polygons")

#     def draw_buttons(self, context, layout):
#         layout.prop(self, "mode_", text="Mode")

    def make_verts(self, nsides, radius, rand_r, rand_phi, rand_seed):
        if rand_r or rand_phi:
            random.seed(rand_seed)

        vertices = []
        dphi = (2*pi)/nsides
        for i in range(nsides):
            phi = dphi * i
            # randomize radius if necessary
            if not rand_r:
                rr = radius
            else:
                rr = random.uniform(radius - rand_r, radius + rand_r)
            # randomize angle if necessary
            if rand_phi:
                phi = random.uniform(phi - rand_phi, phi + rand_phi)
            x = rr*cos(phi)
            y = rr*sin(phi)
            v = (x, y, 0)
            vertices.append(v)
        return vertices

    def make_edges(self, nsides, shift):
        vs = range(nsides)
        # FIXME: do we really need to convert zip object to list here?
        edges = list( zip( vs, rotate(vs, shift+1) ) )
        return edges

    def make_faces(self, nsides, shift):
        # for now, do not return faces if star factor
        # is not zero - the face obviously would be degraded.
        if shift:
            return []
        vs = range(nsides)
        face = list(vs)
        return [face]

    def process(self):
        # inputs
        if self.inputs['Radius'].is_linked:
            radius = SvGetSocketAnyType(self, self.inputs['Radius'])[0]
        else:
            radius = [self.rad_]

        if self.inputs['N Sides'].is_linked:
            nsides = SvGetSocketAnyType(self, self.inputs['N Sides'])[0]
            nsides = list(map(lambda x: max(3, int(x)), Vertices))
        else:
            nsides = [self.sides_]

        if self.inputs['RandomSeed'].is_linked:
            seed = SvGetSocketAnyType(self, self.inputs['Seed'])[0]
        else:
            seed = [self.rand_seed_]

        if self.inputs['RandomR'].is_linked:
            rand_r = SvGetSocketAnyType(self, self.inputs['RandomR'])[0]
        else:
            rand_r = [self.rand_r_]

        if self.inputs['RandomPhi'].is_linked:
            rand_phi = SvGetSocketAnyType(self, self.inputs['RandomPhi'])[0]
        else:
            rand_phi = [self.rand_phi_]

        if self.inputs['Shift'].is_linked:
            shift = SvGetSocketAnyType(self, self.inputs['Shift'])[0]
        else:
            shift = [self.shift_]

        parameters = match_long_repeat([radius, nsides, seed, rand_r, rand_phi, shift])

        # outputs
        if self.outputs['Vertices'].is_linked:
            vertices = [self.make_verts(n, r, dr, dphi, s) for r, n, s, dr, dphi, shift in zip(*parameters)]
            SvSetSocketAnyType(self, 'Vertices', vertices)

        if self.outputs['Edges'].is_linked:
            edges = [self.make_edges(n, shift) for r, n, s, dr, dphi, shift in zip(*parameters)]
            SvSetSocketAnyType(self, 'Edges', edges)

        if self.outputs['Polygons'].is_linked:
            faces = [self.make_faces(n, shift) for r, n, s, dr, dphi, shift in zip(*parameters)]
            SvSetSocketAnyType(self, 'Polygons', faces)


def register():
    bpy.utils.register_class(SvNGonNode)


def unregister():
    bpy.utils.unregister_class(SvNGonNode)

