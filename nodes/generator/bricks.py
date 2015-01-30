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
from bpy.props import BoolProperty, IntProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (fullList, match_long_repeat, updateNode)

class Vertex(object):
    def __init__(self, u, v):
        self.index = None
        self.u = u
        self.v = v
    
    def __lt__(self, other):
        return self.u < other.u

class VEdge(object):
    def __init__(self, v1, v2):
        self.v1 = v1
        self.v2 = v2

def select(line, v1, v2):
    return [v.index for v in sorted(line) if v.u > v1.u and v.u < v2.u]

class SvBricksNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Bricks '''
    bl_idname = 'SvBricksNode'
    bl_label = 'Bricks'
    bl_icon = 'OUTLINER_OB_EMPTY'

    du_ = FloatProperty(name='Unit width', description='One brick width',
            default=2.0, min=0.0,
            update=updateNode)
    dv_ = FloatProperty(name='Unit heigth', description='One brick height',
            default=1.0, min=0.0,
            update=updateNode)
    sizeu_ = FloatProperty(name='Width', description='Grid width',
            default=10.0, min=0.0,
            update=updateNode)
    sizev_ = FloatProperty(name='Height', description='Grid height',
            default=10.0, min=0.0,
            update=updateNode)
    toothing_ = FloatProperty(name='Toothing',
            description='Bricks toothing amount',
            default=0.0,
            update=updateNode)
    toothing_r_ = FloatProperty(name='Toothing Random',
            description='Bricks toothing randomization factor',
            default=0.0, min=0.0, max=1.0,
            update=updateNode)
    rdu_ = FloatProperty(name='Random U',
            description='Randomization amplitude along width',
            default=0.0, min=0.0,
            update=updateNode)
    rdv_ = FloatProperty(name='Random V',
            description='Randomization amplitude along height',
            default=0.0, min=0.0,
            update=updateNode)
    shift_ = FloatProperty(name='Shift',
            description='Bricks shifting factor',
            default=0.5, min=0.0, max=1.0,
            update=updateNode)
    rand_seed_ = IntProperty(name='Seed', description='Random seed',
            default=0,
            update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "DU").prop_name = 'du_'
        self.inputs.new('StringsSocket', "DV").prop_name = 'dv_'
        self.inputs.new('StringsSocket', "SizeU").prop_name = 'sizeu_'
        self.inputs.new('StringsSocket', "SizeV").prop_name = 'sizev_'
        self.inputs.new('StringsSocket', "Toothing").prop_name = 'toothing_'
        self.inputs.new('StringsSocket', "ToothingR").prop_name = 'toothing_r_'
        self.inputs.new('StringsSocket', "RDU").prop_name = 'rdu_'
        self.inputs.new('StringsSocket', "RDV").prop_name = 'rdv_'
        self.inputs.new('StringsSocket', "Shift").prop_name = 'shift_'
        self.inputs.new('StringsSocket', "RandomSeed").prop_name = 'rand_seed_'

        self.outputs.new('VerticesSocket', "Vertices")
        self.outputs.new('StringsSocket', "Edges")
        self.outputs.new('StringsSocket', "Polygons")

    def process(self):
        if not self.outputs['Vertices'].is_linked:
            return

        # inputs
        dus = self.inputs['DU'].sv_get()[0]
        dvs = self.inputs['DV'].sv_get()[0]
        sizeus = self.inputs['SizeU'].sv_get()[0]
        sizevs = self.inputs['SizeV'].sv_get()[0]
        toothings = self.inputs['Toothing'].sv_get()[0]
        toothingrs = self.inputs['ToothingR'].sv_get()[0]
        rdus = self.inputs['RDU'].sv_get()[0]
        rdvs = self.inputs['RDV'].sv_get()[0]
        shifts = self.inputs['Shift'].sv_get()[0]

        seeds = self.inputs['RandomSeed'].sv_get()[0]

        result_vertices = []
        result_edges = []
        result_faces = []

        parameters = match_long_repeat([dus, dvs, sizeus, sizevs, toothings, toothingrs, rdus, rdvs, shifts, seeds])
        for du,dv,sizeu,sizev,toothing,toothing_r, rdu, rdv, shift, seed in zip(*parameters):

            random.seed(seed)

            vs = []
            v = 0.0
            while v <= sizev:
                vs.append(v + random.uniform(-rdv, rdv))
                v += dv

            ulines = [set() for v in vs]
            vedges = [[] for i in range(len(vs)-1)]
            for i,v in enumerate(vs[:-1]):
                if i%2 == 0:
                    u = 0.0
                else:
                    u = shift * du
                j = 0
                while u <= sizeu:
                    t1 = toothing*random.uniform(1.0-toothing_r, 1.0)
                    t2 = toothing*random.uniform(1.0-toothing_r, 1.0)
                    vt1 = Vertex(u, v+t1)
                    vt2 = Vertex(u, vs[i+1]-t2)
                    ulines[i].add(vt1)
                    ulines[i+1].add(vt2)
                    edge = VEdge(vt1, vt2)
                    vedges[i].append(edge)
                    u += du
                    u += random.uniform(-rdu, rdu)
                    j += 1

            idx = 0
            vertices = []
            for line in ulines:
                for vt in line:
                    vt.index = idx
                    idx += 1
                    vertices.append((vt.u, vt.v, 0.0))

            edges = []
            for line in ulines:
                lst = sorted(line)
                for v1,v2 in zip(lst, lst[1:]):
                    edges.append((v1.index, v2.index))

            for lst in vedges:
                for edge in lst:
                    edges.append((edge.v1.index, edge.v2.index))

            faces = []
            for i, lst in enumerate(vedges):
                line1 = ulines[i]
                line2 = ulines[i+1]
                for e1,e2 in zip(lst, lst[1:]):
                    face = [e1.v2.index, e1.v1.index]
                    face.extend(select(line1, e1.v1, e2.v1)) 
                    face.extend([e2.v1.index, e2.v2.index])
                    face.extend(reversed(select(line2, e1.v2, e2.v2)))
                    faces.append(face)

            result_vertices.append(vertices)
            result_edges.append(edges)
            result_faces.append(faces)

        # outputs
        if self.outputs['Vertices'].is_linked:
            self.outputs['Vertices'].sv_set(result_vertices)

        if self.outputs['Edges'].is_linked:
            self.outputs['Edges'].sv_set(result_edges)

        if self.outputs['Polygons'].is_linked:
            self.outputs['Polygons'].sv_set(result_faces)


def register():
    bpy.utils.register_class(SvBricksNode)


def unregister():
    bpy.utils.unregister_class(SvBricksNode)


