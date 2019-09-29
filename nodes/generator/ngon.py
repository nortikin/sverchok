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
from sverchok.data_structure import (fullList, match_long_repeat, updateNode, rotate_list)

def make_verts(nsides, radius, rand_r, rand_phi, rand_seed, divs):
    if rand_r or rand_phi:
        random.seed(rand_seed)

    vertices = []
    dphi = (2*pi)/nsides
    prev_vertex = None
    first_vertex = None
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
        next_vertex = (x, y, 0)
        if prev_vertex is not None and divs > 1:
            prev_x, prev_y, prev_z = prev_vertex
            alphas = [float(i)/divs for i in range(1, divs)]
            mid_vertices = [((1-alpha)*prev_x + alpha*x, (1-alpha)*prev_y + alpha*y, 0) for alpha in alphas]
            vertices.extend(mid_vertices)
        vertices.append(next_vertex)
        prev_vertex = next_vertex
        if first_vertex is None:
            first_vertex = next_vertex

    if divs > 1 and first_vertex is not None and prev_vertex is not None:
        x, y, z = first_vertex
        prev_x, prev_y, prev_z = prev_vertex
        alphas = [float(i)/divs for i in range(1, divs)]
        mid_vertices = [((1-alpha)*prev_x + alpha*x, (1-alpha)*prev_y + alpha*y, 0) for alpha in alphas]
        vertices.extend(mid_vertices)
    return vertices

def make_edges(nsides, shift, divs):
    vs = range(nsides*divs)
    edges = list( zip( vs, rotate_list(vs, shift+1) ) )
    return edges

def make_faces(nsides, shift, divs):
    # for now, do not return faces if star factor
    # is not zero - the face obviously would be degraded.
    if shift:
        return []
    vs = range(nsides*divs)
    face = list(vs)
    return [face]

class SvNGonNode(bpy.types.Node, SverchCustomTreeNode):
    ''' NGon '''
    bl_idname = 'SvNGonNode'
    bl_label = 'NGon'
    bl_icon = 'RNDCURVE'
    sv_icon = 'SV_NGON'

    rad_: FloatProperty(name='Radius', description='Radius',
                         default=1.0,
                         update=updateNode)
    sides_: IntProperty(name='N Sides', description='Number of polygon sides',
                        default=5, min=3,
                        update=updateNode)
    divisions : IntProperty(name='Divisions', description = "Number of divisions to divide each side to",
                        default=1, min=1,
                        update=updateNode)
    rand_seed_: FloatProperty(name='Seed', description='Random seed',
                        default=0.0,
                        update=updateNode)
    rand_r_: FloatProperty(name='RandomR', description='Radius randomization amplitude',
                        default=0.0, min=0.0,
                        update=updateNode)
    rand_phi_: FloatProperty(name='RandomPhi', description='Angle randomization amplitude (radians)',
                        default=0.0, min=0.0, max=pi,
                        update=updateNode)
    shift_: IntProperty(name='Shift', description='Edges bind shift (star factor)',
                        default=0, min=0,
                        update=updateNode)             

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'rad_'
        self.inputs.new('SvStringsSocket', "N Sides").prop_name = 'sides_'
        self.inputs.new('SvStringsSocket', "Divisions").prop_name = 'divisions'
        self.inputs.new('SvStringsSocket', "RandomR").prop_name = 'rand_r_'
        self.inputs.new('SvStringsSocket', "RandomPhi").prop_name = 'rand_phi_'
        self.inputs.new('SvStringsSocket', "RandomSeed").prop_name = 'rand_seed_'
        self.inputs.new('SvStringsSocket', "Shift").prop_name = 'shift_'

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Polygons")

    def process(self):
        # inputs
        radius = self.inputs['Radius'].sv_get()[0]

        nsides = self.inputs['N Sides'].sv_get()[0]
        nsides = list(map(lambda x: max(3, int(x)), nsides))

        seed = self.inputs['RandomSeed'].sv_get()[0]

        rand_r   = self.inputs['RandomR'].sv_get()[0]
        rand_phi = self.inputs['RandomPhi'].sv_get()[0]

        shift = self.inputs['Shift'].sv_get()[0]

        if 'Divisions' in self.inputs:
            divisions = self.inputs['Divisions'].sv_get()[0]
        else:
            divisions = [1]

        parameters = match_long_repeat([radius, nsides, seed, rand_r, rand_phi, shift, divisions])

        # outputs
        if self.outputs['Vertices'].is_linked:
            vertices = [make_verts(n, r, dr, dphi, s, divs) for r, n, s, dr, dphi, shift, divs in zip(*parameters)]
            self.outputs['Vertices'].sv_set(vertices)

        if self.outputs['Edges'].is_linked:
            edges = [make_edges(n, shift, divs) for r, n, s, dr, dphi, shift, divs in zip(*parameters)]
            self.outputs['Edges'].sv_set(edges)

        if self.outputs['Polygons'].is_linked:
            faces = [make_faces(n, shift, divs) for r, n, s, dr, dphi, shift, divs in zip(*parameters)]
            self.outputs['Polygons'].sv_set(faces)


def register():
    bpy.utils.register_class(SvNGonNode)


def unregister():
    bpy.utils.unregister_class(SvNGonNode)
