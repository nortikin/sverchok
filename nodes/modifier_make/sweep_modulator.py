# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
# import mathutils
# from mathutils import Vector
# from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.core.handlers import get_sv_depsgraph, set_sv_depsgraph_need

class SvSweepModulator(bpy.types.Node, SverchCustomTreeNode):
    
    """
    Triggers: SvSweepModulator
    Tooltip: 
    
    A short description for reader of node code
    """

    bl_idname = 'SvSweepModulator'
    bl_label = 'Sweep Modulator'
    bl_icon = 'GREASEPENCIL'

    construct_name: bpy.props.StringProperty(name="construct_name", update=updateNode)
    active: bpy.props.BoolProperty(update=updateNode)

    def sv_init(self, context):
        self.inputs.new("SvStringsSocket", "Factor")
        self.inputs.new("SvObjectsSocket", "Shape A")
        self.inputs.new("SvObjectsSocket", "Shape B")
        self.inputs.new("SvObjectsSocket", "Trajectory")
        self.outputs.new("SvVerticesSocket", "Verts")
        self.outputs.new("SvStringsSocket", "Edges")
        self.outputs.new("SvStringsSocket", "Faces")

    def draw_buttons(self, context, layout):
        ...

    def sweep_between(self, construct):
        self.ensure_bevels(construct)

        # -- get verts without depsgraph, just path verts
        path_obj = bpy.data.objects.get(construct.traject.name)
        path_obj_data = path_obj.to_mesh()
        path_verts = [v.co for v in path_obj_data.vertices]
        num_path_verts = len(path_verts)

        # -- use the depsgraph for the beveled objects
        sv_depsgraph = get_sv_depsgraph()
        shape_a = sv_depsgraph.objects[construct.shape_a.name]
        shape_b = sv_depsgraph.objects[construct.shape_b.name]
        shape_a_data = shape_a.to_mesh()
        shape_b_data = shape_b.to_mesh()
        shape_a_verts = [v.co for v in shape_a_data.vertices]
        shape_b_verts = [v.co for v in shape_b_data.vertices]
        num_verts_shape_a = len(shape_a_verts)
        num_verts_shape_b = len(shape_b_verts)

        if num_verts_shape_a == num_verts_shape_b:
            extruded_data_a = obj.to_mesh(preserve_all_data_layers=True, depsgraph=sv_depsgraph)
            extruded_data_b = obj.to_mesh(preserve_all_data_layers=True, depsgraph=sv_depsgraph)

            verts_a = [v.co for v in extruded_data_a.vertices]
            verts_b = [v.co for v in extruded_data_b.vertices]

            # -- perform mix
            verts_final = self.mix(verts_a, verts_b, construct.factors, divider=num_verts_shape_a)

            # -- because both A and B should have identical topology, we'll copy A's edges/faes.
            edges = extruded_data_a.edge_keys
            faces = [list(p.vertices) for p in extruded_data_a.polygons]

        else:
           print("nope, they are not the same topology, ideally you will use PolyLine Viewer output")

        # -- cleanup
        path_obj.to_mesh_clear()
        shape_a.to_mesh_clear()
        shape_b.to_mesh_clear()



        


    def process(self):
        """
        [ ] make / ensure collection destination ready
        [ ] duplicate trajectory into collection (twice)
        [ ] ensure vertex/node count of Shapes are identical if not.
        [ ] assign Shapes (bevel objects) A, B to trajectories (path)
        [ ] pickup the resulting geometry (like object in does) for both
            paths, and prepare for numpy to interpolate between them
        [ ] provide virtual Shape index shifting,
              - shifts the vertices in-situ of A or B to match the other
              - to avoid awkward surface twisting.
        [ ] apply the factor (list) to each pair of profiles from start to end
        [ ] hide dummy objects option.
        [ ] output result V E F.
        """
        if not all([self.active, self.construct_name]):
            return
        
        construct = lambda: None
        construct.complete = False
        try:
            construct.name = self.construct_name
            construct.factors = self.inputs["Factor"].sv_get()[0]
            construct.shape_a = self.inputs["Shape A"].sv_get()[0]
            construct.shape_b = self.inputs["Shape B"].sv_get()[0]
            construct.traject = self.inputs["Trajectory"].sv_get()[0]
            construct.complete = True

        finally:
            if not construct.complete:
                return
            
            set_sv_depsgraph_need(True)
            v, e, f = self.sweep_between(construct)
            self.outputs['Verts'].sv_set([v])
            self.outputs['Edges'].sv_set([e])
            self.outputs['Faces'].sv_set([f])

    def free(self):
        set_sv_depsgraph_need(False)        


classes = [SvSweepModulator]
register, unregister = bpy.utils.register_classes_factory(classes)
