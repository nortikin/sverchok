# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.core.handlers import get_sv_depsgraph, set_sv_depsgraph_need


class SvSweepModulator(bpy.types.Node, SverchCustomTreeNode):

    """
    Triggers: SvSweepModulator
    Tooltip: 
    """

    bl_idname = 'SvSweepModulator'
    bl_label = 'Sweep Modulator'
    bl_icon = 'GP_MULTIFRAME_EDITING'

    construct_name: bpy.props.StringProperty(name="construct_name", update=updateNode)
    active: bpy.props.BoolProperty(update=updateNode)

    def sv_init(self, context):
        inew = self.inputs.new
        inew("SvStringsSocket", "Factor")
        inew("SvObjectsSocket", "Shape A")
        inew("SvObjectsSocket", "Shape B")
        inew("SvObjectsSocket", "Trajectory")
        onew = self.outputs.new
        onew("SvVerticesSocket", "Verts")
        onew("SvStringsSocket", "Edges")
        onew("SvStringsSocket", "Faces")

    def draw_buttons(self, context, layout):
        ...

    def ensure_collection(self):
        collections = bpy.data.collections
        if not collections.get(self.construct_name):
            collection = collections.new(self.construct_name)
            bpy.context.scene.collection.children.link(collection)
        return collections.get(self.construct_name)

    def get_trajectory_object(self, collection, trajectory_named):
        objects = bpy.data.objects
        if trajectory_named in objects:
            traject = objects[trajectory_named]
        else:
            traject = construct.traject.copy()
            traject.data = construct.traject.data.copy()
            traject.name = trajectory_named
            collection.objects.link(traject)
        return traject

    def ensure_bevels(self, construct):
        # -- create new collection, if not yet present
        collection = self.ensure_collection()
        
        # -- duplicate trajectory twice into the collection, if not yet present
        traject_name_a = construct_name + ".A"
        traject_name_b = construct_name + ".B"
        traject_a = self.get_trajectory_object(collection, trajectory_name_a)
        traject_b = self.get_trajectory_object(collection, trajectory_name_b)
        
        # -- attach shapes A,B to trajectories A,B, as bevel objects, 
        traject_a.bevel_object = construct.shape_a
        traject_b.bevel_object = construct.shape_b

        # -- add extrusions as extrusion_a + extrusion_b to construct
        construct.extrusion_a = traject_a
        construct.extrusion_b = traject_b


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

            # -- get vertices
            extruded_data_a = construct.extrusion_a.to_mesh(preserve_all_data_layers=True, depsgraph=sv_depsgraph)
            extruded_data_b = construct.extrusion_b.to_mesh(preserve_all_data_layers=True, depsgraph=sv_depsgraph)
            verts_a = [v.co for v in extruded_data_a.vertices]
            verts_b = [v.co for v in extruded_data_b.vertices]

            # -- perform mix
            verts_final = self.mix(verts_a, verts_b, construct.factors, divider=num_verts_shape_a)

            # -- because both A and B should have identical topology, we'll copy A's edges/faes.
            edges = extruded_data_a.edge_keys
            faces = [list(p.vertices) for p in extruded_data_a.polygons]

            # -- cleanup
            construct.extrusion_a.to_mesh_clear()
            construct.extrusion_b.to_mesh_clear()

        else:
           print("nope, they are not the same topology, ideally you will use PolyLine Viewer output")

        # -- cleanup
        path_obj.to_mesh_clear()
        shape_a.to_mesh_clear()
        shape_b.to_mesh_clear()

    def mix(verts_a, verts_b, factors, divider=0):
        if len(factors) != divider:
            if len(factors) > divider:
                factors = factors[:divider]
            else:
                num_to_add = divider - len(factors)
                padding = [factors[-1]] * num_to_add
                factors.extend(padding)


    def process(self):
        """
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
            with self.sv_throttle_tree_update():
                v, e, f = self.sweep_between(construct)
                self.outputs['Verts'].sv_set([v])
                self.outputs['Edges'].sv_set([e])
                self.outputs['Faces'].sv_set([f])

    def free(self):
        set_sv_depsgraph_need(False)        


classes = [SvSweepModulator]
register, unregister = bpy.utils.register_classes_factory(classes)
