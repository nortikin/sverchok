# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from sverchok.node_tree import SverchCustomTreeNode
from .line import Mesh

import sverchok.utils.cython as cyt


class SvMeshToObjectNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers:
    Tooltip:
    """
    bl_idname = 'SvMeshToObjectNode'
    bl_label = 'Mesh to Object'

    def sv_init(self, context):
        self.inputs.new('SvMeshSocket', "Mesh")
        self.outputs.new('SvObjectSocket', "Object")

    def process(self):
        if not cyt.IS_COMPILED:
            raise RuntimeError("Source code was not sompiled")

        # No vectorization here
        me: Mesh = self.inputs["Mesh"].sv_get(deepcopy=False, default=None)
        if me is None:
            return

        obj = bpy.data.objects.get('Temp')
        if not obj:
            obj = bpy.data.objects.new('Temp', bpy.data.meshes.new('Temp'))
            bpy.context.scene.collection.objects.link(obj)

        obj.data.clear_geometry()
        obj.data.vertices.add(len(me.verts))
        obj.data.vertices.foreach_set("co", np.ravel(me.verts))

        cyt.mesh.py_test(obj.data, me.verts.tolist())

        calc_edges = False
        obj.data.update(calc_edges_loose=calc_edges)
        self.outputs['Object'].sv_set([obj])
    
    # pure Python
    def _process(self):
        # No vectorization here
        me: Mesh = self.inputs["Mesh"].sv_get(deepcopy=False)

        obj = bpy.data.objects.get('Temp')
        if not obj:
            obj = bpy.data.objects.new('Temp', bpy.data.meshes.new('Temp'))
            bpy.context.scene.collection.objects.link(obj)

        if len(obj.data.vertices) == len(me.verts):
            obj.data.vertices.foreach_set("co", np.ravel(me.verts))
        else:
            obj.data.clear_geometry()
            obj.data.vertices.add(len(me.verts))
            obj.data.vertices.foreach_set("co", np.ravel(me.verts))

            if len(me.faces_start):
                obj.data.loops.add(len(me.loop_vert))
                obj.data.loops.foreach_set('vertex_index', me.loop_vert.tolist())
                # obj.data.loops.foreach_set('edge_index', me.loop_edge)
                obj.data.polygons.add(len(me.faces_start))
                obj.data.polygons.foreach_set('loop_start', me.faces_start.tolist())
                obj.data.polygons.foreach_set('loop_total', me.faces_total.tolist())
            elif len(me.edges):
                obj.data.edges.add(len(me.edges))
                obj.data.edges.foreach_set('vertices', np.ravel(me.edges))

                # print(me.edges)
                # obj.data.edges.add(len(me.edges) // 2)
                # obj.data.edges.foreach_set('vertices', me.edges)

        calc_edges = (not len(me.faces_start)) and bool(len(me.edges))
        obj.data.update(calc_edges_loose=calc_edges)
        self.outputs['Object'].sv_set([obj])


def register():
    bpy.utils.register_class(SvMeshToObjectNode)


def unregister():
    bpy.utils.unregister_class(SvMeshToObjectNode)
