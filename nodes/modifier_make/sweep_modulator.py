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


def interp_v3l_v3v3(a, b, t):
    """ interpolate an np array between two states """
    if t == 0.0: return a
    elif t == 1.0: return b
    else: return ((1.0 - t) * a) + (t * b)


class SvSweepModulator(bpy.types.Node, SverchCustomTreeNode):

    """
    Triggers: SvSweepModulator
    Tooltip: 
    """

    bl_idname = 'SvSweepModulator'
    bl_label = 'Sweep Modulator'
    bl_icon = 'GP_MULTIFRAME_EDITING'

    construct_name: bpy.props.StringProperty(name="construct_name", update=updateNode)
    active: bpy.props.BoolProperty(name="active", update=updateNode)
    modifying_factors: bpy.props.BoolProperty(name="modifying_factors")

    interpolate: bpy.props.BoolProperty(name="interpolate smooth", update=updateNode)

    def sv_init(self, context):
        inew = self.inputs.new
        inew("SvStringsSocket", "Factor")
        inew("SvObjectSocket", "Shape A")
        inew("SvObjectSocket", "Shape B")
        inew("SvObjectSocket", "Trajectory")
        onew = self.outputs.new
        onew("SvVerticesSocket", "Verts")
        onew("SvStringsSocket", "Edges")
        onew("SvStringsSocket", "Faces")

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "active", text="UPDATE")
        row = layout.row(align=True)
        row.prop(self, "construct_name", text="", icon="EXPERIMENTAL")
        row = layout.row(align=True)
        row.alert = self.modifying_factors
        row.prop(self, "interpolate", text="Interpolate Factors", icon="SHADERFX")

    def ensure_collection(self):
        collections = bpy.data.collections
        if not collections.get(self.construct_name):
            collection = collections.new(self.construct_name)
            bpy.context.scene.collection.children.link(collection)
        return collections.get(self.construct_name)

    def get_trajectory_object(self, collection, construct, ident):
        objects = bpy.data.objects
        trajectory_named = construct.name + "." + ident

        if trajectory_named in objects:
            traject = objects[trajectory_named]
            traject.data = construct.traject.data.copy()
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
        traject_a = self.get_trajectory_object(collection, construct, "A")
        traject_b = self.get_trajectory_object(collection, construct, "B")

        # -- attach shapes A,B to trajectories A,B, as bevel objects, 
        traject_a.data.bevel_object = construct.shape_a
        traject_b.data.bevel_object = construct.shape_b

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

        # -- use the depsgraph for the bevelled objects
        sv_depsgraph = get_sv_depsgraph()
        shape_a = sv_depsgraph.objects[construct.shape_a.name]
        shape_b = sv_depsgraph.objects[construct.shape_b.name]
        shape_a_data = shape_a.to_mesh()
        shape_b_data = shape_b.to_mesh()

        num_verts_shape_a = len(shape_a_data.vertices)
        num_verts_shape_b = len(shape_b_data.vertices)

        if num_verts_shape_a == num_verts_shape_b:

            # -- get vertices
            extrusion_a = sv_depsgraph.objects[construct.extrusion_a.name]
            extrusion_b = sv_depsgraph.objects[construct.extrusion_b.name]
            extruded_data_a = extrusion_a.to_mesh(preserve_all_data_layers=True, depsgraph=sv_depsgraph)
            extruded_data_b = extrusion_b.to_mesh(preserve_all_data_layers=True, depsgraph=sv_depsgraph)
            verts_a = [v.co[:] for v in extruded_data_a.vertices]
            verts_b = [v.co[:] for v in extruded_data_b.vertices]
            
            # -- perform mix
            verts_final = self.mix(verts_a, verts_b, construct.factors, divider=num_verts_shape_a)

            # -- because both A and B should have identical topology, we'll copy A's edges/faces.
            edges = extruded_data_a.edge_keys
            faces = [list(p.vertices) for p in extruded_data_a.polygons]

            # -- cleanup
            extrusion_a.to_mesh_clear()
            extrusion_b.to_mesh_clear()
            return verts_final, edges, faces

        else:
           print("nope, they are not the same topology, ideally you will use PolyLine Viewer output")

        # -- cleanup
        path_obj.to_mesh_clear()
        shape_a.to_mesh_clear()
        shape_b.to_mesh_clear()

    def mix(self, verts_a, verts_b, factors, divider=0):
        splits = int(len(verts_a) / divider)
        
        self.modifying_factors = False

        if len(factors) != splits:
            self.modifying_factors = True
            
            if self.interpolate:
                tvals = np.linspace(0, 1, splits)
                factors = np.interp(tvals, factors, factors).tolist()
            else:
                if len(factors) > splits:
                    factors = factors[:splits]
                else:
                    num_to_add = splits - len(factors)
                    padding = [factors[-1]] * num_to_add
                    factors.extend(padding)

        np_verts_a = np.array(verts_a)
        np_verts_b = np.array(verts_b)
        split_num = np_verts_a.shape[0] / divider
        vlist_a = np.split(np_verts_a, split_num)
        vlist_b = np.split(np_verts_b, split_num)
        # print(len(vlist_a), len(vlist_b), len(factors))
        vlist_mix = []
        _ = [vlist_mix.extend(interp_v3l_v3v3(*p).tolist()) for p in zip(vlist_a, vlist_b, factors)]
        return vlist_mix
    

    def process(self):
        """
        [ ] provide virtual Shape index shifting,
              - shifts the vertices in-situ of A or B to match the other
              - to avoid awkward surface twisting.
        [ ] hide dummy objects option.   seems tricky. or ugly.  use the outliner for now.
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
