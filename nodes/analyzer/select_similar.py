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

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty
from mathutils import Vector
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, fullList
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
from sverchok.utils.modules.polygon_utils import areas_from_polygons, pols_perimeters
from sverchok.utils.modules.edge_utils import edges_length, edges_direction, adjacent_faces_number, faces_angle
from sverchok.utils.modules.vertex_utils import adjacent_edg_pol_num

def equals(val, orig_val, threshold):
    return orig_val - threshold <= val <= orig_val + threshold


def less_or_equal(val, orig_val, threshold):
    return val <= orig_val + threshold


def more_or_equal(val, orig_val, threshold):
    return orig_val - threshold <= val


def equal_vectors(val, orig_val, threshold):
    are_equal = True
    for v, ov in zip(val, orig_val):
        are_equal = are_equal and (ov - threshold <= v <= ov + threshold)
    return are_equal

def coplanar_pols(val, orig_val, threshold):
    equal_normals = equal_vectors(val[0], orig_val[0], threshold)
    if equal_normals:
        vector_base = Vector(val[1])- Vector(orig_val[1])
        distance = vector_base.dot(Vector(val[0]))
        return abs(distance) < threshold
    else:
        return False

class SvSelectSimilarNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Similar Sel
    Tooltip: Select vertices, edges, faces similar to selected ones

    Like Blender's Shift+G
    """

    bl_idname = 'SvSelectSimilarNode'
    bl_label = 'Select similar'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SELECT_SIMILAR'

    modes = [
        ("verts", "Vertices", "Select similar vertices", 0),
        ("edges", "Edges", "Select similar edges", 1),
        ("faces", "Faces", "Select similar faces", 2)
    ]

    vertex_modes = [
        ("0", "Normal", "Select vertices with similar normal", 0),
        ("1", "Adjacent faces", "Select vertices with similar number of adjacent faces", 1),
        # SIMVERT_VGROUP is skipped for now, since we do not have vgroups at input
        ("3", "Adjacent edges", "Select vertices with similar number of adjacent edges", 3)
    ]

    edge_modes = [
        ("101", "Length", "Select edges with similar length", 101),
        ("102", "Direction", "Select edges with similar direction", 102),
        ("103", "Adjacent faces", "Select edges with similar number of faces around edge", 103),
        ("104", "Face Angle", "Select edges by face angle", 104)
        # SIMEDGE_CREASE, BEVEL, SEAM, SHARP, FREESTYLE are skipped for now,
        # since we do not have such data at input
    ]

    face_modes = [
        # SIMFACE_MATERIAL, IMAGE are skipped for now, since we do not have such data at input
        ("203", "Area", "Select faces with similar area", 203),
        ("204", "Sides", "Select faces with similar number of sides", 204),
        ("205", "Perimeter", "Select faces with similar perimeter", 205),
        ("206", "Normal", "Select faces with similar normal", 206),
        ("207", "CoPlanar", "Select coplanar faces", 207)
        # SIMFACE_SMOOTH, FREESTYLE are skipped for now too
    ]

    cmp_modes = [
        ("0", "=", "Compare by ==", 0),
        ("1", ">=", "Compare by >=", 1),
        ("2", "<=", "Compare by <=", 2)
    ]

    def update_mode(self, context):
        for mode in self.modes:
            if self.mode != mode[0]:
                if not self.outputs[mode[1]].hide_safe:
                    self.outputs[mode[1]].hide_safe = True
            else:
                if self.outputs[mode[1]].hide_safe:
                    self.outputs[mode[1]].hide_safe = False

        updateNode(self, context)

    mode: EnumProperty(name ="Select",
            items=modes,
            default="faces",
            update=update_mode)

    vertex_mode: EnumProperty(name="Select by",
            items=vertex_modes,
            default="0",
            update=update_mode)
    edge_mode: EnumProperty(name="Select by",
            items=edge_modes,
            default="101",
            update=update_mode)
    face_mode: EnumProperty(name="Select by",
            items=face_modes,
            default="203",
            update=update_mode)

    compare: EnumProperty(name="Compare by",
            items=cmp_modes,
            default="0",
            update=update_mode)

    threshold: FloatProperty(name="Threshold",
            min=0.0, default=0.1,
            update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=True)

        if self.mode == "verts":
            layout.prop(self, "vertex_mode")
        elif self.mode == "edges":
            layout.prop(self, "edge_mode")
        elif self.mode == "faces":
            layout.prop(self, "face_mode")

        layout.prop(self, "compare", expand=True)

    def sv_init(self, context):
        inew = self.inputs.new
        inew('SvVerticesSocket', "Vertices")
        inew('SvStringsSocket', "Edges")
        inew('SvStringsSocket', "Faces")
        inew('SvStringsSocket', "Mask")
        inew('SvStringsSocket', "Threshold").prop_name = "threshold"

        onew = self.outputs.new
        onew('SvStringsSocket', "Mask")
        onew('SvVerticesSocket', "Vertices")
        onew('SvStringsSocket', "Edges")
        onew('SvStringsSocket', "Faces")

        self.update_mode(context)

    def set_up_verts(self, vertices, edges, faces, compare_func):

        if int(self.vertex_mode) == 0:
            bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
            vals = [tuple(v.normal) for v in bm.verts]
            bm.free()
            compare_func = equal_vectors
        elif int(self.vertex_mode) == 1:
            vals = adjacent_edg_pol_num(vertices, faces)
        elif int(self.vertex_mode) == 3:
            vals = adjacent_edg_pol_num(vertices, edges)

        return vals, compare_func

    def set_up_edges(self, vertices, edges, faces, compare_func):
        if int(self.edge_mode) == 101:
            vals = edges_length(vertices, edges, sum_length=False, out_numpy=False)
        elif int(self.edge_mode) == 102:
            vals = edges_direction(vertices, edges, out_numpy=False)
            compare_func = equal_vectors
        elif int(self.edge_mode) == 103:
            vals = adjacent_faces_number(edges, faces)
        elif int(self.edge_mode) == 104:
            bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
            normals = [tuple(face.normal) for face in bm.faces]
            bm.free()
            vals = faces_angle(normals, edges, faces)

        return vals, compare_func

    def set_up_pols(self, vertices, edges, faces, compare_func):
        if int(self.face_mode) == 203:
            vals = areas_from_polygons(vertices, faces, sum_faces=False)
        elif int(self.face_mode) == 204:
            vals = [len(p) for p in faces]
        elif int(self.face_mode) == 205:
            vals = pols_perimeters(vertices, faces)
        elif  int(self.face_mode) == 206:
            bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
            vals = [tuple(face.normal) for face in bm.faces]
            bm.free()
            compare_func = equal_vectors
        elif  int(self.face_mode) == 207:
            bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
            vals = [[tuple(bm_face.normal), vertices[face[0]]] for bm_face, face in zip(bm.faces, faces)]
            bm.free()
            compare_func = coplanar_pols

        return vals, compare_func

    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Faces'].sv_get(default=[[]])
        masks_s = self.inputs['Mask'].sv_get(default=[[1]])
        thresholds = self.inputs['Threshold'].sv_get()[0]

        result_verts = []
        result_edges = []
        result_faces = []
        result_mask = []

        meshes = match_long_repeat([vertices_s, edges_s, faces_s, masks_s, thresholds])
        compare_funcs = [equals, more_or_equal, less_or_equal]
        compare_func = compare_funcs[int(self.compare)]
        info_funcs = {
            'verts': self.set_up_verts,
            'edges': self.set_up_edges,
            'faces': self.set_up_pols
        }
        info_func = info_funcs[self.mode]
        for vertices, edges, faces, masks, threshold in zip(*meshes):
            selected_faces = []
            selected_vertices = []
            selected_edges = []
            out_mask = []
            selected_vals = []

            if self.mode == 'verts':
                components = vertices
                selected_components = selected_vertices

            elif self.mode == 'edges':
                components = edges
                selected_components = selected_edges

            elif self.mode == 'faces':
                components = faces
                selected_components = selected_faces


            vals, compare_func = info_func(vertices, edges, faces, compare_func)
            fullList(masks, len(components))
            fullList(thresholds, len(components))
            selected_vals = [val for mask, val in zip(masks, vals) if mask]

            for mask, component, val in zip(masks, components, vals):
                if mask:
                    selected_components.append(component)
                    out_mask.append(True)
                else:
                    select = False
                    for val_s in selected_vals:
                        if compare_func(val, val_s, threshold):
                            selected_components.append(component)
                            out_mask.append(True)
                            select = True
                            break
                    if not select:
                        out_mask.append(False)


            result_verts.append(selected_vertices)
            result_edges.append(selected_edges)
            result_faces.append(selected_faces)
            result_mask.append(out_mask)




        self.outputs['Mask'].sv_set(result_mask)
        self.outputs['Vertices'].sv_set(result_verts)
        self.outputs['Edges'].sv_set(result_edges)
        self.outputs['Faces'].sv_set(result_faces)

def register():
    bpy.utils.register_class(SvSelectSimilarNode)


def unregister():
    bpy.utils.unregister_class(SvSelectSimilarNode)
