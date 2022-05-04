# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from itertools import chain

import numpy as np

import bpy
from sverchok.data_structure import numpy_full_list, numpy_full_list_cycle
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.mesh.data_structure import Mesh
import sverchok.utils.cython as cyt



class SvLimeMeshNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: mesh line
    Tooltip: Generate simple line
    """
    bl_idname = 'SvLimeMeshNode'
    bl_label = 'Line'

    def sv_init(self, context):
        s = self.inputs.new('SvStringsSocket', "Number")
        s.use_prop = True
        s.default_property_type = 'int'
        s.default_int_property = 2
        self.inputs.new('SvVerticesSocket', "Vertices").use_prop = True
        s = self.inputs.new('SvVerticesSocket', "Vertices")
        s.use_prop = True
        s.default_property = (1, 0, 0)
        self.outputs.new('SvMeshSocket', "Mesh")

    def process2(self):
        n = np.asarray(self.inputs["Number"].sv_get(deepcopy=False)[0], dtype=np.int64)
        v1 = np.asarray(self.inputs[1].sv_get(deepcopy=False)[0], dtype=np.float32)
        v2 = np.asarray(self.inputs[2].sv_get(deepcopy=False)[0], dtype=np.float32)

        obj_n = max(len(v1), len(v2))
        n = numpy_full_list_cycle(n, obj_n)
        v1 = numpy_full_list(v1, obj_n)
        v2 = numpy_full_list(v2, obj_n)

        me = Mesh()
        me.verts = create_verts(v1[0], v2[0], n[0])
        me.edges = create_edges(n-1)

        self.outputs["Mesh"].sv_set(me)

    # from sverchok.utils.profile import profile
    # @profile
    def process2(self):
        n = np.asarray(self.inputs["Number"].sv_get(deepcopy=False)[0], dtype=np.int64)
        v1 = np.asarray(self.inputs[1].sv_get(deepcopy=False)[0], dtype=np.float32)
        v2 = np.asarray(self.inputs[2].sv_get(deepcopy=False)[0], dtype=np.float32)

        me = Mesh()
        me.verts = create_verts2(v1, v2, n)

        self.outputs["Mesh"].sv_set(me)

    # from sverchok.utils.profile import profile
    # @profile
    def process(self):
        if not cyt.IS_COMPILED:
            raise RuntimeError("The node is not compiled")
        n = np.asarray(self.inputs["Number"].sv_get(deepcopy=False)[0], dtype=np.int64)
        v1 = np.asarray(self.inputs[1].sv_get(deepcopy=False)[0], dtype=np.float32)
        v2 = np.asarray(self.inputs[2].sv_get(deepcopy=False)[0], dtype=np.float32)

        obj_n = max(len(v1), len(v2))
        n = numpy_full_list_cycle(n, obj_n)
        v1 = numpy_full_list(v1, obj_n)
        v2 = numpy_full_list(v2, obj_n)

        me = Mesh()
        me.verts = cyt.mesh.create_verts3(v1, v2, n)
        me.edges = cyt.mesh.create_edges3(n, obj_n)

        self.outputs["Mesh"].sv_set(me)


def register():
    bpy.utils.register_class(SvLimeMeshNode)


def unregister():
    bpy.utils.unregister_class(SvLimeMeshNode)
