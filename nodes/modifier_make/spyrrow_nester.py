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
from bpy.props import BoolVectorProperty, EnumProperty, BoolProperty, FloatProperty, IntProperty

from sverchok.core.sv_custom_exceptions import SvInvalidInputException, SvInvalidResultException
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import ensure_nesting_level, zip_long_repeat, updateNode
import sverchok.utils.sv_mesh_utils as sv_mesh
from sverchok.utils.spyrrow import SpyrrowSolver
from sverchok.dependencies import spyrrow

def make_edges(n_verts):
    edges = [(i, i+1) for i in range(n_verts-1)]
    edges.append((n_verts-1, 0))
    return edges

class SvSpyrrowNesterNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Spyrrow Nesting Packing
    Tooltip: Solve strip packing (nesting) problems
    """
    bl_idname = 'SvSpyrrowNesterNode'
    bl_label = "Spyrrow Nester"
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_DUAL_MESH'
    sv_dependencies = ['spyrrow']

    activate : BoolProperty(
        name = "Activate",
        default = True,
        update = updateNode)

    early_termination : BoolProperty(
        name = "Allow early termination",
        description = "Whether to allow early termination of the algorithm",
        default = True,
        update = updateNode)

    quadtree_depth : IntProperty(
        name = "Quadtree depth",
        description = "Maximum depth of the quadtree used by the collision detection engine jagua-rs. Must be positive, common values are 3,4,5",
        default = 4,
        min = 1, max = 8,
        update = updateNode)

    min_separation : FloatProperty(
        name = "Separation",
        description = "Minimum required distance between packed items",
        default = 0.0,
        min = 0.0,
        update = updateNode)

    total_time : IntProperty(
        name = "Total time",
        description = "Total time budget in seconds",
        min = 1,
        default = 10,
        update = updateNode)

    use_all_cores : BoolProperty(
        name = "Use all CPU cores",
        default = True,
        update = updateNode)
    
    num_workers : IntProperty(
        name = "Threads",
        description = "Number of threads used by the collision detection engine during exploration",
        default = 4,
        min = 1,
        update = updateNode)

    stripe_height : FloatProperty(
        name = "Strip Height",
        description = "The fixed height of the strip",
        default = 4.0,
        min = 0.0,
        update = updateNode)

    item_count : IntProperty(
        name = "Count",
        default = 1,
        min = 1,
        update = updateNode)

    random_seed : IntProperty(
        name = "Seed",
        default = 0,
        update = updateNode)

    restrict_angle : IntProperty(
        name = "Angle",
        default = 90,
        min = 0,
        update = updateNode)

    rotation_modes = [
        ('NO', "No rotations", "Disallow rotations", 0),
        ('ANY', "Arbitrary rotation", "Arbitrary rotation", 1),
        ('STEP', "Restrict by step", "Restrict rotation by step, e.g. 0, 30, 60...", 2),
        ('ANGLES', "Only specified angles", "Allow rotations by specified angles", 3)
    ]

    planes = [
        ('XY', "XY", "XY plane", 0),
        ('XZ', "XZ", "XZ plane", 1),
        ('YZ', "YZ", "YZ plane", 2)
    ]

    def update_sockets(self, context):
        self.inputs['Angle'].hide_safe = self.rotation_mode in {'NO', 'ANY'}
        updateNode(self, context)

    rotation_mode : EnumProperty(
        name = "Rotation",
        items = rotation_modes,
        default = 'NO',
        update = update_sockets)

    flat_output : BoolProperty(
        name = "Flat output",
        default = True,
        update = updateNode)

    plane : EnumProperty(
        name = "Plane",
        description = "Coordinate plane",
        items = planes,
        default = 'XY',
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'Count').prop_name = 'item_count'
        self.inputs.new('SvStringsSocket', 'StripeHeight').prop_name = 'stripe_height'
        self.inputs.new('SvStringsSocket', 'MinSeparation').prop_name = 'min_separation'
        self.inputs.new('SvStringsSocket', 'Angle').prop_name = 'restrict_angle'
        self.inputs.new('SvStringsSocket', 'Seed').prop_name = 'random_seed'
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvStringsSocket', 'Indices')
        self.outputs.new('SvMatrixSocket', 'Matrices')
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'activate', toggle = True, icon = 'CHECKMARK')
        layout.prop(self, "plane", expand=True)
        layout.label(text="Rotation:")
        layout.prop(self, 'rotation_mode', text='')
        layout.prop(self, 'total_time')
        layout.prop(self, 'early_termination')
        layout.prop(self, 'use_all_cores')
        if not self.use_all_cores:
            layout.prop(self, 'num_workers')
        layout.prop(self, 'flat_output')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'quadtree_depth')

    def get_config(self, min_separation, seed):
        return spyrrow.StripPackingConfig(
                early_termination = self.early_termination,
                quadtree_depth = self.quadtree_depth,
                min_items_separation = min_separation,
                total_computation_time = self.total_time,
                num_workers = self.num_workers if not self.use_all_cores else None,
                seed = seed)

    def sort_verts(self, verts, edges, faces):
        if faces:
            if len(faces) != 1:
                raise SvInvalidInputException("Each item must have exactly one face")
            face = faces[0]
            verts = [verts[j] for j in face]
            return verts
        elif edges:
            verts, _, _ = sv_mesh.sort_vertices_by_connections(verts, edges, True)
            return verts
        else:
            return verts

    def prepare_angles(self, angles):
        #print("Src A", angles)
        if self.rotation_mode == 'NO':
            angles = []
        elif self.rotation_mode == 'ANY':
            angles = None
        elif self.rotation_mode == 'STEP':
            if len(angles) != 1:
                raise SvInvalidInputException("Exactly one angle value must be provided")
            angles = list(range(0, 360, angles[0]))
        #print("Res A", angles)
        return angles

    def process(self):
        if not any((s.is_linked for s in self.outputs)):
            return

        verts_out = []
        edges_out = []
        faces_out = []
        indices_out = []
        matrices_out = []
        if self.activate:
            verts_s = self.inputs['Vertices'].sv_get()
            if self.inputs['Edges'].is_linked:
                edges_s = self.inputs['Edges'].sv_get()
                edges_s = ensure_nesting_level(edges_s, 5)
            else:
                edges_s = [[[0]]]
            if self.inputs['Faces'].is_linked:
                faces_s = self.inputs['Faces'].sv_get()
                faces_s = ensure_nesting_level(faces_s, 5)
            else:
                faces_s = [[[0]]]
            height_s = self.inputs['StripeHeight'].sv_get()
            min_separation_s = self.inputs['MinSeparation'].sv_get()
            seed_s = self.inputs['Seed'].sv_get()
            count_s = self.inputs['Count'].sv_get()
            angle_s = self.inputs['Angle'].sv_get()

            height_s = ensure_nesting_level(height_s, 2)
            min_separation_s = ensure_nesting_level(min_separation_s, 2)
            count_s = ensure_nesting_level(count_s, 3)
            seed_s = ensure_nesting_level(seed_s, 2)
            verts_s = ensure_nesting_level(verts_s, 5)
            angle_s = ensure_nesting_level(angle_s, 4)

            for params in zip_long_repeat(verts_s, edges_s, faces_s, angle_s, count_s, height_s, min_separation_s, seed_s):
                for verts_l, edges_l, faces_l, angle_l, count_l, height, min_separation, seed in zip_long_repeat(*params):
                    config = self.get_config(min_separation, seed)
                    solver = SpyrrowSolver(config, height, plane = self.plane)
                    for verts, edges, faces, angles, count in zip_long_repeat(verts_l, edges_l, faces_l, angle_l, count_l):
                        verts = self.sort_verts(verts, edges, faces)
                        angles = self.prepare_angles(angles)
                        solver.add_item(verts, count = count, allowed_orientations = angles)

                    problem_verts = []
                    problem_edges = []
                    problem_faces = []
                    problem_matrices = []
                    problem_indices = []
                    for item in solver.solve().items():
                        item_verts = item.calc_verts()
                        problem_verts.append(item_verts)
                        edges = make_edges(len(item_verts))
                        problem_edges.append(edges)
                        face = list(range(len(item_verts)))
                        faces = [face]
                        problem_faces.append(faces)
                        problem_matrices.append(item.calc_matrix())
                        problem_indices.append(item.get_index())
                    if self.flat_output:
                        verts_out.extend(problem_verts)
                        edges_out.extend(problem_edges)
                        faces_out.extend(problem_faces)
                        matrices_out.extend(problem_matrices)
                        indices_out.extend([problem_indices])
                    else:
                        verts_out.append(problem_verts)
                        edges_out.append(problem_edges)
                        faces_out.append(problem_faces)
                        matrices_out.append(problem_matrices)
                        indices_out.append([problem_indices])
        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)
        self.outputs['Indices'].sv_set(indices_out)
        self.outputs['Matrices'].sv_set(matrices_out)

def register():
    bpy.utils.register_class(SvSpyrrowNesterNode)

def unregister():
    bpy.utils.unregister_class(SvSpyrrowNesterNode)

