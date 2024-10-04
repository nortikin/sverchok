# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
import bpy
from bpy.props import FloatProperty, BoolProperty, EnumProperty, IntProperty
import bmesh

from sverchok.core.sv_custom_exceptions import SvNoDataError
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, get_data_nesting_level, ensure_nesting_level, zip_long_repeat
from sverchok.utils.bvh_tree import bvh_tree_from_polygons
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.mesh_spatial import populate_mesh_edges, populate_mesh_volume, populate_mesh_surface
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

class SvPopulateMeshNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Populate Mesh
    Tooltip: Generate random points within mesh
    """
    bl_idname = 'SvPopulateMeshNode'
    bl_label = 'Populate Mesh'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_POPULATE_SOLID'

    def update_sockets(self, context):
        self.inputs['FieldMin'].hide_safe = self.proportional_field != True
        self.inputs['FieldMax'].hide_safe = self.proportional_field != True
        self.inputs['RadiusField'].hide_safe = self.distance_mode != 'FIELD'
        self.inputs['MinDistance'].hide_safe = self.distance_mode != 'CONST'
        self.inputs['Weights'].hide_safe = self.gen_mode == 'VOLUME'
        self.outputs['Radiuses'].hide_safe = self.distance_mode != 'FIELD'
        self.outputs['Indices'].hide_safe = self.gen_mode not in {'SURFACE', 'EDGES'}
        updateNode(self, context)

    modes = [
            ('VOLUME', "Volume", "Generate points inside mesh", 0),
            ('SURFACE', "Surface", "Generate points on the surface of the mesj", 1),
            ('EDGES', "Edges", "Generate points on edges", 2)
        ]

    gen_mode : EnumProperty(
            name = "Generation mode",
            items = modes,
            default = 'VOLUME',
            update = update_sockets)

    threshold : FloatProperty(
            name = "Threshold",
            default = 0.5,
            description="The node will not generate points in areas where the value of scalar field is less than this value",
            update = updateNode)

    field_min : FloatProperty(
            name = "Field Minimum",
            default = 0.0,
            description="Minimum value of scalar field reached within the area defined by Bounds input. This input is used to define the probability of vertices generation at certain points",
            update = updateNode)

    field_max : FloatProperty(
            name = "Field Maximum",
            default = 1.0,
            description="Maximum value of scalar field reached within the area defined by Bounds input. This input is used to define the probability of vertices generation at certain points",
            update = updateNode)

    seed: IntProperty(default=0, name='Seed', description="Random seed", update=updateNode)

    count : IntProperty(
            name = "Count",
            default = 50,
            min = 1,
            description="The number of points to be generated",
            update = updateNode)

    proportional_field : BoolProperty(
            name = "Proportional to Field",
            default = False,
            description="If checked, then the points density will be distributed proportionally to the values of scalar field. Otherwise, the points will be uniformly distributed in the area where the value of scalar field exceeds threshold",
            update = update_sockets)

    proportional_faces : BoolProperty(
            name = "Proportional to Face Area",
            default = True,
            description="If checked, then number of points at each face is proportional to the area of the face",
            update = update_sockets)

    min_r : FloatProperty(
            name = "Min.Distance",
            description = "Minimum distance between generated points; set to 0 to disable the check",
            default = 0.0,
            min = 0.0,
            update = updateNode)

    distance_modes = [
            ('CONST', "Min. Distance", "Specify minimum distance between points", 0),
            ('FIELD', "Radius Field", "Specify radius of empty sphere around each point by scalar field", 1)
        ]

    distance_mode : EnumProperty(
            name = "Distance",
            description = "How minimum distance between points is restricted",
            items = distance_modes,
            default = 'CONST',
            update = update_sockets)

    random_radius : BoolProperty(
            name = "Random radius",
            description = "Make sphere radiuses random, restricted by scalar field values",
            default = False,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text='Mode:')
        layout.prop(self, "gen_mode", text='')
        layout.label(text='Distance:')
        layout.prop(self, 'distance_mode', text='')
        layout.prop(self, "proportional_field")
        if self.gen_mode == 'SURFACE':
            layout.prop(self, "proportional_faces", text="Proportional to Face Area")
        elif self.gen_mode == 'EDGES':
            layout.prop(self, "proportional_faces", text="Proportional to Edge Length")
        if self.distance_mode == 'FIELD':
            layout.prop(self, 'random_radius')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Edges")
        self.inputs.new('SvStringsSocket', "Faces")
        self.inputs.new('SvStringsSocket', "Weights")
        self.inputs.new('SvScalarFieldSocket', "Field").enable_input_link_menu = False
        self.inputs.new('SvStringsSocket', "Count").prop_name = 'count'
        self.inputs.new('SvStringsSocket', "MinDistance").prop_name = 'min_r'
        self.inputs.new('SvScalarFieldSocket', "RadiusField")
        self.inputs.new('SvStringsSocket', "Threshold").prop_name = 'threshold'
        self.inputs.new('SvStringsSocket', "FieldMin").prop_name = 'field_min'
        self.inputs.new('SvStringsSocket', "FieldMax").prop_name = 'field_max'
        self.inputs.new('SvStringsSocket', 'Seed').prop_name = 'seed'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Indices")
        self.outputs.new('SvStringsSocket', "Radiuses")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        if self.proportional_field and not self.inputs['Field'].is_linked:
            raise SvNoDataError(socket=self.inputs['Field'], node=self)

        verts_s = self.inputs['Vertices'].sv_get()
        if self.inputs['Edges'].is_linked:
            edges_s = self.inputs['Edges'].sv_get()
            edges_s = ensure_nesting_level(edges_s, 4)
        else:
            edges_s = [[[None]]]
        faces_s = self.inputs['Faces'].sv_get()
        faces_s = ensure_nesting_level(faces_s, 4)
        if self.gen_mode in {'SURFACE', 'EDGES'} and self.inputs['Weights'].is_linked:
            weights_s = self.inputs['Weights'].sv_get()
            weights_s = ensure_nesting_level(weights_s, 3)
        else:
            weights_s = [[None]]
        fields_s = self.inputs['Field'].sv_get(default=[[None]])
        count_s = self.inputs['Count'].sv_get()
        min_r_s = self.inputs['MinDistance'].sv_get()
        threshold_s = self.inputs['Threshold'].sv_get()
        field_min_s = self.inputs['FieldMin'].sv_get()
        field_max_s = self.inputs['FieldMax'].sv_get()
        seed_s = self.inputs['Seed'].sv_get()
        if self.distance_mode == 'FIELD':
            radius_s = self.inputs['RadiusField'].sv_get()
        else:
            radius_s = [[None]]

        input_level = get_data_nesting_level(verts_s)
        verts_s = ensure_nesting_level(verts_s, 4)
        nested_mesh = input_level > 3
        if self.inputs['Field'].is_linked:
            input_level = get_data_nesting_level(fields_s, data_types=(SvScalarField,))
            nested_field = input_level > 1
            fields_s = ensure_nesting_level(fields_s, 2, data_types=(SvScalarField,))
        else:
            nested_field = False
        if self.distance_mode == 'FIELD':
            input_level = get_data_nesting_level(radius_s, data_types=(SvScalarField,))
            nested_radius = input_level > 1
            radius_s = ensure_nesting_level(radius_s, 2, data_types=(SvScalarField,))
        else:
            nested_radius = False
        count_s = ensure_nesting_level(count_s, 2)
        min_r_s = ensure_nesting_level(min_r_s, 2)
        threshold_s = ensure_nesting_level(threshold_s, 2)
        field_min_s = ensure_nesting_level(field_min_s, 2)
        field_max_s = ensure_nesting_level(field_max_s, 2)
        seed_s = ensure_nesting_level(seed_s, 2)

        nested_output = nested_mesh or nested_field or nested_radius

        verts_out = []
        radius_out = []
        indices_out = []
        inputs = zip_long_repeat(verts_s, edges_s, faces_s, weights_s,
                                 fields_s, count_s,
                                 min_r_s, radius_s, threshold_s,
                                 field_min_s, field_max_s, seed_s)

        for objects in inputs:
            new_verts = []
            new_radius = []
            new_indices = []
            for verts, edges, faces, weights, field, count, min_r, radius_field, threshold, field_min, field_max, seed in zip_long_repeat(*objects):
                bm = bmesh_from_pydata(verts, edges, faces, markup_face_data=True)
                if self.gen_mode in {'SURFACE', 'VOLUME'}:
                    bmesh.ops.triangulate(
                        bm, faces=bm.faces, quad_method='FIXED', ngon_method='EAR_CLIP'
                    )
                idxs_layer = bm.faces.layers.int.get("initial_index")
                if weights is not None:
                    weights = [weights[f[idxs_layer]] for f in bm.faces]
                verts, edges, faces = pydata_from_bmesh(bm)
                if seed == 0:
                    seed = 12345
                np.random.seed(seed)
                if self.distance_mode == 'FIELD':
                    min_r = 0
                if self.gen_mode == 'VOLUME':
                    bvh = bvh_tree_from_polygons(verts, faces,
                                                 all_triangles=True,
                                                 epsilon=0.0, safe_check=True)
                    verts, radiuses = populate_mesh_volume(verts, bvh, field, count,
                                                           min_r, radius_field, threshold,
                                                           field_min, field_max,
                                                           proportional_field = self.proportional_field,
                                                           random_radius = self.random_radius,
                                                           seed=seed)
                    verts = np.array(verts).tolist()
                    indices = [None]
                elif self.gen_mode == 'SURFACE':
                    indices, verts, radiuses = populate_mesh_surface(bm, weights, field,
                                                            count, min_r, radius_field,
                                                            threshold,
                                                            field_min, field_max,
                                                            proportional_field = self.proportional_field,
                                                            proportional_faces = self.proportional_faces,
                                                            random_radius = self.random_radius,
                                                            seed=seed)
                else: # EDGES
                    indices, verts, radiuses = populate_mesh_edges(verts, edges, weights,
                                                                   field, count, threshold,
                                                                   field_min, field_max,
                                                                   min_r, radius_field,
                                                                   random_radius = self.random_radius,
                                                                   proportional_field = self.proportional_field,
                                                                   proportional_edges = self.proportional_faces,
                                                                   seed=seed)
                bm.free()

                new_verts.append(verts)
                new_radius.append(radiuses)
                new_indices.append(indices)

            if nested_output:
                verts_out.append(new_verts)
                radius_out.append(new_radius)
                indices_out.append(new_indices)
            else:
                verts_out.extend(new_verts)
                radius_out.extend(new_radius)
                indices_out.extend(new_indices)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Radiuses'].sv_set(radius_out)
        self.outputs['Indices'].sv_set(indices_out)


def register():
    bpy.utils.register_class(SvPopulateMeshNode)


def unregister():
    bpy.utils.unregister_class(SvPopulateMeshNode)

