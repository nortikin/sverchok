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


classes = [SvSweepModulator]
register, unregister = bpy.utils.register_classes_factory(classes)
