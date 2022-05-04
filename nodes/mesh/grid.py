# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from itertools import chain

import numpy as np

import bpy
from sverchok.node_tree import SverchCustomTreeNode
from .line import Mesh


class SvGridMeshNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: mesh line
    Tooltip: Generate simple line
    """
    bl_idname = 'SvGridMeshNode'
    bl_label = 'Grid'

    def sv_init(self, context):
        s = self.inputs.new('SvStringsSocket', "Size X")
        s.use_prop = True
        s.default_float_property = 1
        s = self.inputs.new('SvStringsSocket', "Size Y")
        s.use_prop = True
        s.default_float_property = 1
        s = self.inputs.new('SvStringsSocket', "Number X")
        s.use_prop = True
        s.default_property_type = 'int'
        s.default_int_property = 2
        s = self.inputs.new('SvStringsSocket', "Number Y")
        s.use_prop = True
        s.default_property_type = 'int'
        s.default_int_property = 2
        self.outputs.new('SvMeshSocket', "Mesh")

    def process(self):
        # No vectorization here
        nx = max(self.inputs["Number X"].sv_get(deepcopy=False)[0][0], 2)
        ny = max(self.inputs["Number Y"].sv_get(deepcopy=False)[0][0], 2)
        sx = self.inputs["Size X"].sv_get(deepcopy=False)[0][0]
        sy = self.inputs["Size Y"].sv_get(deepcopy=False)[0][0]

        me = Mesh()
        nt = nx * ny
        x_step = sx/(nx-1)
        x = np.linspace(0, nt-1, nt, dtype=np.float32) % nx * x_step
        y_step = sy/(ny-1)
        y = np.floor(np.linspace(0, (1/nx) * (nt-1), nt, dtype=np.float32)) * y_step
        z = np.zeros(nt, dtype=np.float32)
        me.verts = np.stack((x, y, z), axis=-1)

        l0 = np.ravel(np.arange(nt).reshape(ny, nx)[:-1, :-1])
        l1 = np.ravel(np.arange(nt).reshape(ny, nx)[:-1, 1:])
        l2 = np.ravel(np.arange(nt).reshape(ny, nx)[1:, 1:])
        l3 = np.ravel(np.arange(nt).reshape(ny, nx)[1:, :-1])
        me.loop_vert = np.ravel(np.stack((l0, l1, l2, l3), axis=-1))

        face_total = (nx-1) * (ny-1)
        me.faces_start = np.arange(0, face_total*4, 4)
        me.faces_total = np.repeat(4, face_total)

        # print(f'Loop vert{me.loop_vert}')
        # print(f'Face start{me.faces_start}')
        # print(f'Face total;{me.faces_total}')

        # wright output value
        self.outputs["Mesh"].sv_set(me)


def register():
    bpy.utils.register_class(SvGridMeshNode)


def unregister():
    bpy.utils.unregister_class(SvGridMeshNode)
