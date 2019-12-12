# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import cycle, chain
from time import time

import bpy
import bmesh
from bmesh.ops import inset_individual, remove_doubles

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata


def inset_faces(verts, faces, thickness, depth, edges=None, props=None):
    tm = time()
    if props is None:
        props = set('use_even_offset')
    if len(thickness) == 1 and len(depth) == 1:
        bm_out = bmesh_from_pydata(verts, edges, faces, True)
        # it is creates new faces anyway even if all values are zero
        # returns faces without inner one
        # use_interpolate: Interpolate mesh data: e.g. UV’s, vertex colors, weights, etc.
        res = inset_individual(bm_out, faces=list(bm_out.faces), thickness=thickness[0], depth=depth[0],
                               use_even_offset='use_even_offset' in props, use_interpolate=True,
                               use_relative_offset='use_relative_offset' in props)
    else:
        verts_number = 0
        iter_thick = chain(thickness, cycle([thickness[-1]]))
        iter_depth = chain(depth, cycle([depth[-1]]))
        bm_out = bmesh.new()
        for f, t, d in zip(faces, iter_thick, iter_depth):
            # each instance of bmesh get a lot of operative memory, they should be illuminated as fast as possible
            bm = bmesh_from_pydata([verts[i] for i in f], None, [list(range(len(f)))], True)
            res = inset_individual(bm, faces=list(bm.faces), thickness=t, depth=d,
                                   use_even_offset='use_even_offset' in props, use_interpolate=True,
                                   use_relative_offset='use_relative_offset' in props)
            verts_number += merge_bmeshes(bm_out, verts_number, bm)
            bm.free()
    remove_doubles(bm_out, verts=bm_out.verts, dist=1e-6)
    print("Time: ", time() - tm)
    out_verts = [v.co[:] for v in bm_out.verts]
    out_edges = [[v.index for v in edge.verts] for edge in bm_out.edges]
    out_faces = [[v.index for v in face.verts] for face in bm_out.faces]
    return out_verts, out_edges, out_faces


def merge_bmeshes(bm1, verts_number, bm2):
    new_verts = []
    for i, v in enumerate(bm2.verts):
        new_v = bm1.verts.new(v.co)
        new_v.index = i + verts_number
        new_verts.append(new_v)
    for f in bm2.faces:
        bm1.faces.new([new_verts[v.index] for v in f.verts])
    return len(new_verts)


class SvInsetFaces(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: ...
    Tooltip: ...

    ...
    """
    bl_idname = 'SvInsetFaces'
    bl_label = 'Inset faces'
    bl_icon = 'MESH_GRID'

    bool_properties = ['use_even_offset', 'use_relative_offset']

    thickness: bpy.props.FloatProperty(name="Thickness", default=0.1, min=0.0, update=updateNode,
                                       description="Set the size of the offset.")
    depth: bpy.props.FloatProperty(name="Depth", update=updateNode,
                                   description="Raise or lower the newly inset faces to add depth.")
    use_even_offset: bpy.props.BoolProperty(name="Offset even", default=True, update=updateNode,
                                            description="Scale the offset to give a more even thickness.")
    use_relative_offset: bpy.props.BoolProperty(name="Offset Relative", default=False, update=updateNode,
                                                description="Scale the offset by lengths of surrounding geometry.")

    def draw_buttons(self, context, layout):
        pass

    def draw_buttons_ext(self, context, layout):
        [layout.prop(self, name) for name in self.bool_properties]

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'Thickness').prop_name = 'thickness'
        self.inputs.new('SvStringsSocket', 'Depth').prop_name = 'depth'
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')

    def process(self):
        if not all([sock.is_linked for sock in [self.inputs['Verts'], self.inputs['Faces']]]):
            return
        out = []
        for v, e, f, t, d in zip(self.inputs['Verts'].sv_get(),
                                 self.inputs['Edges'].sv_get() if self.inputs['Edges'].is_linked else cycle([None]),
                                 self.inputs['Faces'].sv_get(), self.inputs['Thickness'].sv_get(),
                                 self.inputs['Depth'].sv_get()):
            out.append(inset_faces(v, f, t, d, e, set(prop for prop in self.bool_properties if getattr(self, prop))))
        out_verts, out_edges, out_faces = zip(*out)
        self.outputs['Verts'].sv_set(out_verts)
        self.outputs['Edges'].sv_set(out_edges)
        self.outputs['Faces'].sv_set(out_faces)


def register():
    bpy.utils.register_class(SvInsetFaces)


def unregister():
    bpy.utils.unregister_class(SvInsetFaces)
