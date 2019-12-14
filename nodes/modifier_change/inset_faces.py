# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import cycle, chain

import bpy
import bmesh
from bmesh.ops import inset_individual, remove_doubles, inset_region

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


def inset_faces(verts, faces, thickness, depth, edges=None, face_data=None, face_mask=None, inset_type=None,
                mask_type=None, props=None):
    """
    It handle Bmesh inset individual and inset region operators according Sverchok demands
    :param verts: list of SV vertices
    :param faces: list of SV faces
    :param thickness: list of floats, at list one value in the list
    :param depth: list of floats, at list one value in the list
    :param edges: list of Edges, optionally
    :param face_data: list of any data related with given faces, optionally
    :param face_mask: list of bool to mark faces in which face should be inserted
    :param inset_type: 'individual' or 'region', 'region by default
    :param mask_type: this option for mask output, should be a set of 3 available keys {'mask', 'out, 'in'}
    :param props: set of properties which should be switched on in bmesh operators
    :return: SV vertices, edges, faces, data related with faces if such was given or indexes of old faces,
    selection mask according given options of mask type
    """
    if mask_type is None:
        mask_type = set()

    # call appropriate inserting function
    if inset_type is None or inset_type == 'individual':
        if len(thickness) == 1 and len(depth) == 1:
            bm_out = inset_faces_individual_one_value(verts, faces, thickness[0], depth[0], edges, face_mask, props)
        else:
            bm_out = inset_faces_individual_multiple_values(verts, faces, thickness, depth, edges, face_mask, props)
    else:
        if len(thickness) == 1 and len(depth) == 1:
            bm_out = inset_faces_region_one_value(verts, faces, thickness[0], depth[0], edges, face_mask, props)
        else:
            bm_out = inset_faces_region_multiple_values(verts, faces, thickness, depth, edges, face_mask, props)

    # convert result Bmesh to Sverchok type
    sv = bm_out.faces.layers.int.get('sv')
    mask = bm_out.faces.layers.int.get('mask')
    out_verts = [v.co[:] for v in bm_out.verts]
    out_edges = [[v.index for v in edge.verts] for edge in bm_out.edges]
    out_faces = [[v.index for v in face.verts] for face in bm_out.faces]
    if face_data:
        face_data_out = [face_data[f[sv]] for f in bm_out.faces]
    else:
        face_data_out = [f[sv] for f in bm_out.faces]
    int_mak = {0: 'in', 1: 'out', 2: 'mask'}
    face_select = [1 if int_mak[f[mask]] in mask_type else 0 for f in bm_out.faces]
    bm_out.free()
    return out_verts, out_edges, out_faces, face_data_out, face_select


def merge_bmeshes(bm1, verts_number, bm2):
    # Merge two Bmeshes into first given, verts_number is total number of vertices of first given bmesh
    # Crete two layers any way and copy data from them to first given Bmesh
    # Returns number of added vertices
    new_verts = []
    sv1 = bm1.faces.layers.int.get('sv')
    sv2 = bm2.faces.layers.int.get('sv')
    mask1 = bm1.faces.layers.int.get('mask')
    mask2 = bm2.faces.layers.int.get('mask')
    for i, v in enumerate(bm2.verts):
        new_v = bm1.verts.new(v.co)
        new_v.index = i + verts_number
        new_verts.append(new_v)
    for f in bm2.faces:
        f1 = bm1.faces.new([new_verts[v.index] for v in f.verts])
        f1[sv1] = f[sv2]
        f1[mask1] = f[mask2]
    return len(new_verts)


def bmesh_from_sv(verts, faces, edges=None, face_int_layers=None):
    # Generate Bmesh from Sverchok data
    # Optionally it can create faces int layers and set given values
    # Layers should be given in dictionary format where ket is name of layer and value as list of values per given faces
    if face_int_layers is None:
        face_int_layers = dict()
    bm = bmesh.new()
    [bm.faces.layers.int.new(key) for key in face_int_layers]
    for i, co in enumerate(verts):
        v = bm.verts.new(co)
        v.index = i
    bm.verts.ensure_lookup_table()
    if edges:
        for e in edges:
            bm.edges.new([bm.verts[i] for i in e])
    for f in faces:
        bm.faces.new([bm.verts[i] for i in f])
    for key in face_int_layers:
        if face_int_layers[key] is not None:
            for v, f in zip(face_int_layers[key], bm.faces):
                f[bm.faces.layers.int.get(key)] = v
    bm.normal_update()
    return bm


def inset_faces_individual_one_value(verts, faces, thickness, depth, edges=None, face_mask=None, props=None):
    # It calling Bmesh function with one value of thickness and depth for all faces
    if props is None:
        props = set('use_even_offset')
    if face_mask is None:
        face_mask = cycle([True])
    else:
        face_mask = [m for m, _ in zip(chain(face_mask, cycle([face_mask[-1]])), range(len(faces)))]

    bm = bmesh_from_sv(verts, faces, edges, face_int_layers={'sv': list(range(len(faces))), 'mask': None})
    mask = bm.faces.layers.int.get('mask')

    for face, m in zip(list(bm.faces), face_mask):
        if not m:
            face[mask] = 2
    if thickness or depth:
        # it is creates new faces anyway even if all values are zero
        # returns faces without inner one
        # use_interpolate: Interpolate mesh data: e.g. UV’s, vertex colors, weights, etc.
        res = inset_individual(bm, faces=[f for f, m in zip(list(bm.faces), face_mask) if m], thickness=thickness,
                               depth=depth, use_even_offset='use_even_offset' in props, use_interpolate=True,
                               use_relative_offset='use_relative_offset' in props)
        for rf in res['faces']:
            rf[mask] = 1
    return bm


def inset_faces_individual_multiple_values(verts, faces, thicknesses, depths, edges=None, face_mask=None, props=None):
    # It generate Bmesh per one face, inset face into it and merge the Bmesh to output Bmesh
    if props is None:
        props = set('use_even_offset')
    if face_mask is None:
        iter_face_mask = cycle([True])
    else:
        iter_face_mask = chain(face_mask, cycle([face_mask[-1]]))

    verts_number = 0
    iter_thick = chain(thicknesses, cycle([thicknesses[-1]]))
    iter_depth = chain(depths, cycle([depths[-1]]))
    bm_out = bmesh.new()
    sv = bm_out.faces.layers.int.new('sv')
    mask = bm_out.faces.layers.int.new('mask')
    for i, (f, m, t, d) in enumerate(zip(faces, iter_face_mask, iter_thick, iter_depth)):
        # each instance of bmesh get a lot of operative memory, they should be illuminated as fast as possible
        bm = bmesh_from_sv([verts[i] for i in f], [list(range(len(f)))],
                           face_int_layers={'sv': [i], 'mask': None})
        mask = bm.faces.layers.int.get('mask')
        if m and (t or d):
            res = inset_individual(bm, faces=list(bm.faces), thickness=t, depth=d,
                                   use_even_offset='use_even_offset' in props, use_interpolate=True,
                                   use_relative_offset='use_relative_offset' in props)
            for rf in res['faces']:
                rf[mask] = 1
        else:
            for face in bm.faces:
                face[mask] = 2
        verts_number += merge_bmeshes(bm_out, verts_number, bm)
        bm.free()
    remove_doubles(bm_out, verts=bm_out.verts, dist=1e-6)
    return bm_out


def inset_faces_region_one_value(verts, faces, thickness, depth, edges=None, face_mask=None, props=None):
    # It inserts faces in region mode with one value of thickness and depth for all mesh
    if props is None:
        props = {'use_even_offset', 'use_boundary'}
    if face_mask is None:
        face_mask = cycle([True])
    bm = bmesh_from_sv(verts, faces, edges, face_int_layers={'sv': list(range(len(faces))), 'mask': None})
    mask = bm.faces.layers.int.get('mask')

    if thickness or depth:
        # use_interpolate: Interpolate mesh data: e.g. UV’s, vertex colors, weights, etc.
        iter_face_mask = chain(face_mask, cycle([face_mask[-1]])) if face_mask is not None else face_mask
        ins_faces = []
        for f, m in zip(list(bm.faces), iter_face_mask):
            if m:
                ins_faces.append(f)
            else:
                f[mask] = 2
        res = inset_region(bm, faces=ins_faces, thickness=thickness,
                           depth=depth, use_interpolate=True, **{k: True for k in props})
        for rf in res['faces']:
            rf[mask] = 1
    return bm


def inset_faces_region_multiple_values(verts, faces, thicknesses, depths, edges=None, face_mask=None, props=None):
    # It split mesh into islands, calculate average value of thickness and depth per island,
    # inserts faces into island and merge mesh into output mesh
    if props is None:
        props = {'use_even_offset', 'use_boundary'}
    if face_mask is None:
        iter_face_mask = cycle([True])
    else:
        iter_face_mask = chain(face_mask, cycle([face_mask[-1]]))
    face_mask = [m for _, m in zip(range(len(faces)), iter_face_mask)]
    thicknesses = [t for _, t in zip(range(len(faces)), chain(thicknesses, cycle([thicknesses[-1]])))]
    depths = [d for _, d in zip(range(len(faces)), chain(depths, cycle([depths[-1]])))]

    bm = bmesh_from_sv(verts, faces, edges, face_int_layers={'sv': list(range(len(faces))), 'mask': None})
    sv = bm.faces.layers.int.get('sv')
    mask = bm.faces.layers.int.get('mask')

    # Split mesh to islands
    islands = []
    ignored_faces = []
    used = set()
    for face in bm.faces:
        if face in used:
            continue
        if not face_mask[face[sv]]:
            ignored_faces.append(face)
            used.add(face)
            continue
        elif not any([thicknesses[face[sv]], depths[face[sv]]]):
            ignored_faces.append(face)
            used.add(face)
            continue
        island = []
        next_faces = [face]
        while next_faces:
            nf = next_faces.pop()
            if nf in used:
                continue
            island.append(nf)
            used.add(nf)
            for edge in nf.edges:
                for twin_face in edge.link_faces:
                    if twin_face not in used:
                        if not face_mask[twin_face[sv]]:
                            ignored_faces.append(twin_face)
                            used.add(twin_face)
                        elif not any([thicknesses[twin_face[sv]], depths[twin_face[sv]]]):
                            ignored_faces.append(twin_face)
                            used.add(twin_face)
                        else:
                            next_faces.append(twin_face)
        islands.append(island)

    # Regenerate mesh from islands
    verts_number = 0
    bm_out = bmesh.new()
    sv_out = bm_out.faces.layers.int.new('sv')
    mask_out = bm_out.faces.layers.int.new('mask')
    for island_faces in islands:
        # each instance of bmesh get a lot of operative memory, they should be illuminated as fast as possible
        bm_isl = bmesh.new()
        sv_isl = bm_isl.faces.layers.int.new('sv')
        mask_isl = bm_isl.faces.layers.int.new('mask')
        used_verts = dict()
        for face in island_faces:
            face_verts = []
            for v in face.verts:
                if v not in used_verts:
                    v_new = bm_isl.verts.new(v.co)
                    used_verts[v] = v_new
                    face_verts.append(v_new)
                else:
                    face_verts.append(used_verts[v])
            face_new = bm_isl.faces.new(face_verts)
            face_new[sv_isl] = face[sv]
            face_new[mask_isl] = face[mask]
        bm_isl.normal_update()

        thick_isl = sum([thicknesses[f[sv_isl]] for f in bm_isl.faces]) / len(island_faces)
        depth_isl = sum([depths[f[sv_isl]] for f in bm_isl.faces]) / len(island_faces)
        res = inset_region(bm_isl, faces=bm_isl.faces, thickness=thick_isl,
                           depth=depth_isl, use_interpolate=True, **{k: True for k in props})
        for rf in res['faces']:
            rf[mask_isl] = 1
        verts_number += merge_bmeshes(bm_out, verts_number, bm_isl)
        bm_isl.free()

    for face in ignored_faces:
        v_news = []
        for v in face.verts:
            v_news.append(bm_out.verts.new(v.co))
        f = bm_out.faces.new(v_news)
        f[sv_out] = face[sv]
        f[mask_out] = 2

    bm.free()
    remove_doubles(bm_out, verts=bm_out.verts, dist=1e-6)
    return bm_out


class SvInsetFaces(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Also can used as extrude
    Tooltip: Analog of Blender inset function

    Most options on N panel
    """
    bl_idname = 'SvInsetFaces'
    bl_label = 'Inset faces'
    bl_icon = 'MESH_GRID'

    bool_properties = ['use_even_offset', 'use_relative_offset', 'use_boundary', 'use_edge_rail', 'use_outset']
    mask_type_items = [(k, k.title(), '') for i, k in enumerate(['mask', 'out', 'in'])]
    inset_type_items = [(k, k.title(), '', i) for i, k in enumerate(['individual', 'region'])]

    thickness: bpy.props.FloatProperty(name="Thickness", default=0.1, min=0.0, update=updateNode,
                                       description="Set the size of the offset.")
    depth: bpy.props.FloatProperty(name="Depth", update=updateNode,
                                   description="Raise or lower the newly inset faces to add depth.")
    use_even_offset: bpy.props.BoolProperty(name="Offset even", default=True, update=updateNode,
                                            description="Scale the offset to give a more even thickness.")
    use_relative_offset: bpy.props.BoolProperty(name="Offset Relative", default=False, update=updateNode,
                                                description="Scale the offset by lengths of surrounding geometry.")
    use_boundary: bpy.props.BoolProperty(name="Boundary ", default=True, update=updateNode,
                                         description='Determines whether open edges will be inset or not.')
    use_edge_rail: bpy.props.BoolProperty(name="Edge Rail", update=updateNode,
                                          description="Created vertices slide along the original edges of the inner"
                                                      " geometry, instead of the normals.")
    use_outset: bpy.props.BoolProperty(name="Outset ", update=updateNode,
                                       description="Create an outset rather than an inset. Causes the geometry to be "
                                                   "created surrounding selection (instead of within).")
    mask_type: bpy.props.EnumProperty(items=mask_type_items, update=updateNode, options={'ENUM_FLAG'}, default={'out'},
                                description="Switch between untouched, inner and outer faces generated by insertion")
    inset_type: bpy.props.EnumProperty(items=inset_type_items, update=updateNode,
                                       description="Switch between inserting type")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'inset_type', expand=True)

    def draw_buttons_ext(self, context, layout):
        [layout.prop(self, name) for name in self.bool_properties]

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'Face data')
        self.inputs.new('SvStringsSocket', 'Face mask')
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
        for v, e, f, t, d, fd, m in zip(self.inputs['Verts'].sv_get(),
                         self.inputs['Edges'].sv_get() if self.inputs['Edges'].is_linked else cycle([None]),
                         self.inputs['Faces'].sv_get(),
                         self.inputs['Thickness'].sv_get(),
                         self.inputs['Depth'].sv_get(),
                         self.inputs['Face data'].sv_get() if self.inputs['Face data'].is_linked else cycle([None]),
                         self.inputs['Face mask'].sv_get() if self.inputs['Face mask'].is_linked else cycle([None])):
            out.append(inset_faces(v, f, t, d, e, fd, m, self.inset_type, self.mask_type,
                                   set(prop for prop in self.bool_properties if getattr(self, prop))))
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
