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

    def decompose(self, construct):
        ...

    def decompose_both(self, construct):
        num_trajectory_verts = self.get_object("Trajectory", construct.traject)
        profile_a = self.get_object("Shape", construct.shape_a)
        profile_b = self.get_object("Shape", construct.shape_b)
        if not self.same_count(profile_a, profile_b):
            print("nope, they are not the same topology, ideally you will use PolyLine Viewer output")
            return

    def sweep_between(self, construct):
        self.ensure_bevels(construct)
        v1, v2, e1, e2, f1, f2 = self.decompose_both(construct)


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
            
            v, e, f = self.sweep_between(construct)
            self.outputs['Verts'].sv_set([v])
            self.outputs['Edges'].sv_set([e])
            self.outputs['Faces'].sv_set([f])

        


classes = [SvSweepModulator]
register, unregister = bpy.utils.register_classes_factory(classes)
