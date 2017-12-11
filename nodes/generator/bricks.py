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
import collections

import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (fullList, match_long_repeat, updateNode)

"""
The grid is represented by following structure:
 
 V axis

 ^
 |
 |  ----------o-------------------o----------------o----------  <-- ULine
 |            |                   |                |
 |          VEdge              VEdge            VEdge   
 |            |                   |                |
 |  ----o-----o---------o---------o------o---------o------o---  <-- ULine
 |      |               |                |                |
 |    VEdge          VEdge            VEdge             VEdge
 |      |               |                |                |
 |  ----o---------------o----------------o----------------o---  <-- ULine
 |
 O---------------------------------------------------------------------------> U axis
"""

class Vertex(object):
    """
    Object representing a vertex of the grid in U-V coordinate plane.
    """
    def __init__(self, u, v):
        self._index = None
        self.replacement = None
        self.u = u
        self.v = v

    def set_index(self, index):
        self._index = index

    def get_index(self):
        if self.replacement is not None:
            return self.replacement.index
        else:
            return self._index

    index = property(get_index, set_index)

    def __str__(self):
        if self.index is not None:
            return "<" + str(self.index) + ">"
        else:
            return "<{:.4}, {:.4}>".format(self.u, self.v)

    def __repr__(self):
        return str(self)
    
    def __lt__(self, other):
        return self.u < other.u

# #     def __eq__(self, other):
#         return self.u == other.u and self.v == other.v
# 
#     def __hash__(self):
#         return hash(self.u) + hash(self.v)
    
# #     def vector(self):
#         return Vector((self.u, self.v, 0.0))

class VEdge(object):
    """
    Class representing a vertical edge between two bricks.
    The edge connects two vertices.
    """
    def __init__(self, v1, v2):
        self.v1 = v1
        self.v2 = v2
    
    def __str__(self):
        return str(self.v1) + " - " + str(self.v2)

class ULine(object):
    """
    Class representing horiszontal line between rows of bricks.
    Such line goes through the set of vertices.
    """
    def __init__(self, lst):
        self.list = sorted(lst, key=lambda v: v.u)
        self.coords = [v.u for v in self.list]

    def __str__(self):
        return str(self.list)
    
    def iter(self):
        return self.list.iter()

    def __getitem__(self, i):
        return self.list[i]

    def __str__(self):
        return str(self.list)

    def __repr__(self):
        return str(self.list)

    def is_empty(self):
        return len(self.list) == 0

    def remove_by_index(self, idx):
        del self.list[idx]
        del self.coords[idx]

    def get_by_u(self, u):
        for vertex in self.list:
            if vertex.u == u:
                return vertex
        return None

    def select_index(self, v1, v2):
        if v2 < v1:
            return list(reversed([v.index for v in self.list if v.u < v2.u or v.u > v1.u]))
        else:
            return [v.index for v in self.list if v.u > v1.u and v.u < v2.u]

    def select_v(self, v1, v2):
        if v2 < v1:
            return list(reversed([v for v in self.list if v.u < v2.u or v.u > v1.u]))
        else:
            return [v for v in self.list if v.u > v1.u and v.u < v2.u]


def get_center(vertices):
    n = float(len(vertices))
    cu = sum([v.u for v in vertices]) / n
    cv = sum([v.v for v in vertices]) / n
    return Vertex(cu, cv)

def select_index(line, v1, v2):
    return [v.index for v in line if v.u > v1.u and v.u < v2.u]

def select_v(line, v1, v2):
    return [v for v in line if v.u > v1.u and v.u < v2.u]

class SvBricksNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Bricks
    Tooltip: Create a brick wall or honeycomb-like structure.
    """
    bl_idname = 'SvBricksNode'
    bl_label = 'Bricks grid'
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

    cycle_u = BoolProperty(name = "Cycle U",
            description = "Cycle edges and faces in U direction",
            default = False,
            update=updateNode)
    cycle_v = BoolProperty(name = "Cycle v",
            description = "Cycle edges and faces in V direction",
            default = False,
            update=updateNode)


    faces_modes = [
            ("flat", "Flat", "Flat polygons", 0),
            ("stitch", "Stitch", "Stitch with triangles", 1),
            ("centers", "Centers", "Connect each edge with face center", 2)
        ]

    def available_face_modes(self, context):
        result = self.faces_modes[:]
        if self.cycle_u or self.cycle_v:
            del result[-1]
        return result

    faces_mode = EnumProperty(name="Faces",
            description="Faces triangularization mode",
            items = available_face_modes,
            update=updateNode)

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "cycle_u", toggle=True)
        row.prop(self, "cycle_v", toggle=True)
        layout.prop(self, "faces_mode")

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
        self.outputs.new('VerticesSocket', "Centers")

    def process(self):
        if not (self.outputs['Vertices'].is_linked or self.outputs['Centers'].is_linked):
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
        result_centers = []

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

            if self.cycle_v:
                # Merge lists of vertices in first and last ULine
                def update(uline1, uline2):
                    for vertex in uline1:
                        other_vertex = None
                        for o in uline2:
                            if o.u == vertex.u and o.v != vertex.v:
                                other_vertex = o

                        if other_vertex is not None:
                            if vertex.replacement is None:
                                uline2.remove(other_vertex)
                                other_vertex.replacement = vertex
                        else:
                            uline2.add(vertex)

                update(ulines[0], ulines[-1])
                update(ulines[-1], ulines[0])
                if len(ulines[0]) == 0:
                    del ulines[0]
                if len(ulines[-1]) == 0:
                    del ulines[-1]

            ulines = [(ULine(line)) for line in ulines]

            if self.cycle_u:
                # Make each ULine cyclic
                for uline in ulines:
                    last = uline[-1]
                    last.replacement = uline[0]
                    uline.remove_by_index(-1)

            # Assign indicies to vertices
            vertex_idx = 0
            vertices = []
            for line in ulines:
                for vt in line:
                    if vt.replacement is not None:
                        continue
                    new_vertex = (vt.u, vt.v, 0.0)
                    if new_vertex in vertices:
                        continue
                    vt.index = vertex_idx
                    vertex_idx += 1
                    vertices.append(new_vertex)

            edges = []
            for line in ulines:
                for v1,v2 in zip(line, line[1:]):
                    edges.append((v1.index, v2.index))

            for lst in vedges:
                for edge in lst:
                    edges.append((edge.v1.index, edge.v2.index))

            faces = []
            centers = []
            for i, lst in enumerate(vedges):
                line1 = ulines[i]
                line2 = ulines[(i+1) % len(ulines)]
                v_edge_pairs = list(zip(lst, lst[1:]))
                if self.cycle_u:
                    v_edge_pairs.append((lst[-1], lst[0]))
                for e1,e2 in v_edge_pairs:
                    face_vertices = [e1.v2, e1.v1]
                    face_vertices.extend(line1.select_v(e1.v1, e2.v1))
                    face_vertices.extend([e2.v1, e2.v2])
                    face_vertices.extend(reversed(line2.select_v(e1.v2, e2.v2)))
                    center = get_center(face_vertices)
                    centers.append((center.u, center.v, 0.0))

                    if self.faces_mode == "flat":
                        face = [v.index for v in face_vertices]
                        faces.append(face)
                    elif self.faces_mode == "stitch":
                        vs1 = line1.select_index(e1.v1, e2.v1) + [e2.v1.index]
                        vs2 = [e1.v2.index] + line2.select_index(e1.v2, e2.v2) + [e2.v2.index]
                        prev = e1.v1.index
                        alt = e1.v2.index
                        i = 0
                        j = 0
                        first = True
                        while i < len(vs1) and j < len(vs2):
                            vt1 = vs1[i]
                            vt2 = vs2[j]
                            face = [prev, vt1, vt2]
                            faces.append(face)
                            if not first:
                                if i < len(vs1)-1:
                                    prev = vs1[i]
                                    i += 1
                                else:
                                    prev = vs2[j]
                                    j += 1
                            else:
                                if j < len(vs2)-1:
                                    prev = vs2[j]
                                    j += 1
                                else:
                                    prev = vs1[i]
                                    i += 1
                            first = not first
                    elif self.faces_mode == "centers":
                        vertices.append((center.u, center.v, 0.0))
                        center.index = vertex_idx
                        vertex_idx += 1
                        for v1, v2 in zip(face_vertices, face_vertices[1:]):
                            face = [v1.index, v2.index, center.index]
                            faces.append(face)
                        face = [face_vertices[-1].index, face_vertices[0].index, center.index]
                        faces.append(face)

            # With cycling, it may appear that we enumerated the same vertex index
            # in one face twice.
            if self.cycle_u or self.cycle_v:
                faces = [list(collections.OrderedDict.fromkeys(face)) for face in faces]

            result_vertices.append(vertices)
            result_edges.append(edges)
            result_faces.append(faces)
            result_centers.append(centers)

        # outputs
        if self.outputs['Vertices'].is_linked:
            self.outputs['Vertices'].sv_set(result_vertices)

        if self.outputs['Edges'].is_linked:
            self.outputs['Edges'].sv_set(result_edges)

        if self.outputs['Polygons'].is_linked:
            self.outputs['Polygons'].sv_set(result_faces)

        if self.outputs['Centers'].is_linked:
            self.outputs['Centers'].sv_set(result_centers)


def register():
    bpy.utils.register_class(SvBricksNode)


def unregister():
    bpy.utils.unregister_class(SvBricksNode)


