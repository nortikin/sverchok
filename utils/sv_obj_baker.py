# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from bpy.props import StringProperty
from mathutils import Vector, Matrix

from sverchok.data_structure import node_id, dataCorrect

cache_viewer_baker = {}

def fill_cache(node):
    n_id = node_id(node)
    data = node.get_data()

    vertex_ref = n_id + 'v'
    edg_ref = n_id + 'e'
    pol_ref = n_id + 'p'
    matrix_ref = n_id + 'm'
    cache_viewer_baker[vertex_ref] = data[3]
    cache_viewer_baker[edg_ref] = data[1]
    cache_viewer_baker[pol_ref] = data[2]
    cache_viewer_baker[matrix_ref] = data[4]


class SvObjBakeMK3(bpy.types.Operator):
    """ B A K E   OBJECTS """
    bl_idname = "node.sverchok_mesh_baker_mk3"
    bl_label = "Sverchok mesh baker mk3"
    bl_options = {'REGISTER', 'UNDO'}

    idname: StringProperty(
        name='idname',
        description='name of parent node',
        default='')

    idtree: StringProperty(
        name='idtree',
        description='name of parent tree',
        default='')

    def execute(self, context):

        node_group = bpy.data.node_groups[self.idtree]
        node = node_group.nodes[self.idname]
        nid = node_id(node)

        node.fill_cache()
        matrix_cache = cache_viewer_baker[nid + 'm']
        vertex_cache = cache_viewer_baker[nid + 'v']
        edg_cache = cache_viewer_baker[nid + 'e']
        pol_cache = cache_viewer_baker[nid + 'p']

        if matrix_cache and not vertex_cache:
            return {'CANCELLED'}

        v = dataCorrect(vertex_cache)
        e = self.dataCorrect3(edg_cache)
        p = self.dataCorrect3(pol_cache)
        m = self.dataCorrect2(matrix_cache, v)
        self.config = node
        self.makeobjects(v, e, p, m)
        return {'FINISHED'}

    def dataCorrect2(self, destination, obj):
        if destination:
            return destination
        return [Matrix() for v in obj]

    def dataCorrect3(self, destination, fallback=[]):
        if destination:
            return dataCorrect(destination)
        return fallback

    def makeobjects(self, vers, edg, pol, mats):
        objects = {}
        for i, m in enumerate(mats):
            v, e, p = vers[i], edg[i], pol[i]
            objects[str(i)] = self.makemesh(i, v, e, p, m)

        for ob, me in objects.values():
            bpy.context.scene.collection.objects.link(ob)

    def validate_indices(self, ident_num, v, idx_list, kind_list):
        outlist = []
        n = len(v)
        for idx, sublist in enumerate(idx_list):
            tlist = sublist
            if min(sublist) < 0:
                tlist = [(i if i >= 0 else n + i) for i in sublist]
                print('vdmk3 input fixing, converted negative indices to positive')
                print(sublist, ' ---> ', tlist)

            outlist.append(tlist)
        return outlist

    def makemesh(self, i, v, e, p, m):
        name = 'Sv_' + str(i)
        me = bpy.data.meshes.new(name)
        e = self.validate_indices(i, v, e, "edges")
        p = self.validate_indices(i, v, p, "polygons")
        me.from_pydata(v, e, p)
        ob = bpy.data.objects.new(name, me)
        if self.config.extended_matrix:
            ob.data.transform(m)
        else:
            ob.matrix_world = m
        ob.show_name = False
        ob.hide_select = False
        return ob, me

classes = [SvObjBakeMK3]
register, unregister = bpy.utils.register_classes_factory(classes)