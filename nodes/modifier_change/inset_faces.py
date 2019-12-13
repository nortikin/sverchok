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


def inset_faces(verts, faces, thickness, depth, edges=None, face_data=None, mask_type=None, props=None):
    tm = time()
    if len(thickness) == 1 and len(depth) == 1:
        bm_out = inset_faces_individual_one_value(verts, faces, thickness[0], depth[0], edges, props)
    else:
        bm_out = inset_faces_individual_multiple_values(verts, faces, thickness, depth, edges, props)
    print("Time: ", time() - tm)

    sv = bm_out.faces.layers.int.get('sv')
    mask = bm_out.faces.layers.int.get('mask')
    out_verts = [v.co[:] for v in bm_out.verts]
    out_edges = [[v.index for v in edge.verts] for edge in bm_out.edges]
    out_faces = [[v.index for v in face.verts] for face in bm_out.faces]
    if face_data:
        face_data_out = [face_data[f[sv]] for f in bm_out.faces]
    else:
        face_data_out = []
    face_select = [f[mask] if 'out' == mask_type else int(not bool(f[mask])) for f in bm_out.faces]
    bm_out.free()
    return out_verts, out_edges, out_faces, face_data_out, face_select


def merge_bmeshes(bm1, verts_number, layer_item, face_index, bm2):
    new_verts = []
    sv = bm1.faces.layers.int.get('sv')
    mask1 = bm1.faces.layers.int.get('mask')
    mask2 = bm2.faces.layers.int.get('mask')
    for i, v in enumerate(bm2.verts):
        new_v = bm1.verts.new(v.co)
        new_v.index = i + verts_number
        new_verts.append(new_v)
    for f in bm2.faces:
        f1 = bm1.faces.new([new_verts[v.index] for v in f.verts])
        f1[sv] = face_index
        f1[mask1] = f[mask2]
    return len(new_verts)


def inset_faces_individual_one_value(verts, faces, thickness, depth, edges=None, props=None):
    if props is None:
        props = set('use_even_offset')

    bm = bmesh.new()
    sv = bm.faces.layers.int.new('sv')
    mask = bm.faces.layers.int.new('mask')
    for i, co in enumerate(verts):
        v = bm.verts.new(co)
        v.index = i
    bm.verts.ensure_lookup_table()
    if edges:
        for e in edges:
            bm.edges.new([bm.verts[i] for i in e])
    for fi, f in enumerate(faces):
        bmf = bm.faces.new([bm.verts[i] for i in f])
        bmf[sv] = fi
    bm.normal_update()

    if thickness or depth:
        # it is creates new faces anyway even if all values are zero
        # returns faces without inner one
        # use_interpolate: Interpolate mesh data: e.g. UV’s, vertex colors, weights, etc.
        res = inset_individual(bm, faces=list(bm.faces), thickness=thickness, depth=depth,
                               use_even_offset='use_even_offset' in props, use_interpolate=True,
                               use_relative_offset='use_relative_offset' in props)
        for rf in res['faces']:
            rf[mask] = 1
    return bm


def inset_faces_individual_multiple_values(verts, faces, thicknesses, depths, edges=None, props=None):
    if props is None:
        props = set('use_even_offset')

    verts_number = 0
    iter_thick = chain(thicknesses, cycle([thicknesses[-1]]))
    iter_depth = chain(depths, cycle([depths[-1]]))
    bm_out = bmesh.new()
    sv = bm_out.faces.layers.int.new('sv')
    mask = bm_out.faces.layers.int.new('mask')
    for fi, (f, t, d) in enumerate(zip(faces, iter_thick, iter_depth)):
        # each instance of bmesh get a lot of operative memory, they should be illuminated as fast as possible
        bm = bmesh_from_pydata([verts[i] for i in f], edges, [list(range(len(f)))], True)
        mask = bm.faces.layers.int.new('mask')
        if t or d:
            res = inset_individual(bm, faces=list(bm.faces), thickness=t, depth=d,
                                   use_even_offset='use_even_offset' in props, use_interpolate=True,
                                   use_relative_offset='use_relative_offset' in props)
            for rf in res['faces']:
                rf[mask] = 1
        verts_number += merge_bmeshes(bm_out, verts_number, sv, fi, bm)
        bm.free()
    remove_doubles(bm_out, verts=bm_out.verts, dist=1e-6)
    return bm_out


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
    mask_type_items = [(k ,k , '', i) for i, k in enumerate(['out', 'in'])]

    thickness: bpy.props.FloatProperty(name="Thickness", default=0.1, min=0.0, update=updateNode,
                                       description="Set the size of the offset.")
    depth: bpy.props.FloatProperty(name="Depth", update=updateNode,
                                   description="Raise or lower the newly inset faces to add depth.")
    use_even_offset: bpy.props.BoolProperty(name="Offset even", default=True, update=updateNode,
                                            description="Scale the offset to give a more even thickness.")
    use_relative_offset: bpy.props.BoolProperty(name="Offset Relative", default=False, update=updateNode,
                                                description="Scale the offset by lengths of surrounding geometry.")
    mask_type: bpy.props.EnumProperty(items=mask_type_items, update=updateNode,
                                      description="Switch between inner and outer faces generated by insertion")

    def draw_buttons(self, context, layout):
        pass

    def draw_buttons_ext(self, context, layout):
        [layout.prop(self, name) for name in self.bool_properties]

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'Face data')
        self.inputs.new('SvStringsSocket', 'Thickness').prop_name = 'thickness'
        self.inputs.new('SvStringsSocket', 'Depth').prop_name = 'depth'
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvStringsSocket', 'Face data')
        self.outputs.new('SvStringsSocket', 'Mask').custom_draw = 'draw_mask_socket'

    def draw_mask_socket(self, socket, context, layout):
        layout.prop(self, 'mask_type', expand=True)
        layout.label(text=socket.name)

    def process(self):
        if not all([sock.is_linked for sock in [self.inputs['Verts'], self.inputs['Faces']]]):
            return
        out = []
        for v, e, f, t, d, fd in zip(self.inputs['Verts'].sv_get(),
                         self.inputs['Edges'].sv_get() if self.inputs['Edges'].is_linked else cycle([None]),
                         self.inputs['Faces'].sv_get(),
                         self.inputs['Thickness'].sv_get(),
                         self.inputs['Depth'].sv_get(),
                         self.inputs['Face data'].sv_get() if self.inputs['Face data'].is_linked else cycle([None])):
            out.append(inset_faces(v, f, t, d, e, fd, self.mask_type, set(prop for prop in self.bool_properties if getattr(self, prop))))
        out_verts, out_edges, out_faces, out_face_data, out_mask = zip(*out)
        self.outputs['Verts'].sv_set(out_verts)
        self.outputs['Edges'].sv_set(out_edges)
        self.outputs['Faces'].sv_set(out_faces)
        self.outputs['Face data'].sv_set(out_face_data)
        self.outputs['Mask'].sv_set(out_mask)


def register():
    bpy.utils.register_class(SvInsetFaces)


def unregister():
    bpy.utils.unregister_class(SvInsetFaces)
