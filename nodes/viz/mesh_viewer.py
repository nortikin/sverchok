# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import numpy as np
from itertools import cycle
import collections
from random import random as rnd_float

import bpy
from bpy.props import BoolProperty
from mathutils import Matrix, Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import fullList, updateNode
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.sv_obj_helper import SvObjHelper, get_random_init_v3
from sverchok.utils.modules.sv_bmesh_ops import find_islands_treemap
from sverchok.utils.nodes_mixins.generating_objects import BlenderObjects, SvMeshData
from sverchok.utils.handle_blender_data import correct_collection_length


def get_vertex_color_layer(obj):
    vcols = obj.data.vertex_colors

    vertex_color = vcols.get('SvCol')
    return vertex_color or vcols.new(name='SvCol')


def get_random_colors(n):
    return [[rnd_float(), ] * 3 + [1.0] for i in range(n)]


def set_vertices(obj, islands):
    vcols = obj.data.vertex_colors
    loops = obj.data.loops
    loop_count = len(loops)

    # [x] generate random colors set for each island
    num_colors = len(islands)

    # [ ] set seed here
    random_colors = get_random_colors(num_colors)

    # [x] acquire vertex color layer from object
    vertex_color = get_vertex_color_layer(obj)

    # [x] generate mapping from index to island color
    # this is the slower part
    islands_lookup = {}
    for isle_num, isle_set in islands.items():
        for vert_idx in isle_set:
            islands_lookup[vert_idx] = isle_num

    vertex_index = np.zeros(loop_count, dtype=int)
    loops.foreach_get("vertex_index", vertex_index)

    num_components = 4  # ( r g b , not a )
    colors = np.empty(loop_count * num_components, dtype=np.float32)
    colors.shape = (loop_count, num_components)

    idx_lookup = collections.defaultdict(list)
    for idx, v_idx in enumerate(vertex_index):
        idx_lookup[v_idx].append(idx)

    for idx, island in islands_lookup.items():
        colors[idx_lookup[idx]] = random_colors[island]

    colors.shape = (loop_count * num_components,)
    vertex_color.data.foreach_set("color", colors)
    obj.data.update()


def default_mesh(name):
    return bpy.data.meshes.new(name)


def make_bmesh_geometry(node, obj_index, context, verts, *topology):
    collection = context.scene.collection
    meshes = bpy.data.meshes
    objects = bpy.data.objects
    islands = None

    edges, faces, materials, matrix = topology
    name = f'{node.basedata_name}.{obj_index:04d}'

    if name in objects:
        sv_object = objects[name]
    else:
        temp_mesh = default_mesh(name)
        sv_object = objects.new(name, temp_mesh)
        collection.objects.link(sv_object)

    # book-keeping via ID-props!? even this is can be broken by renames
    sv_object['idx'] = obj_index
    sv_object['madeby'] = node.name
    sv_object['basedata_name'] = node.basedata_name

    mesh = sv_object.data
    current_count = len(mesh.vertices)
    propose_count = len(verts)
    difference = (propose_count - current_count)

    ''' With this mode you make a massive assumption about the
        constant state of geometry. Assumes the count of verts
        edges/faces stays the same, and only updates the locations

        node.fixed_verts is not suitable for initial object creation
        but if over time you find that the only change is going to be
        vertices, this mode can be switched to to increase efficiency
    '''
    if node.fixed_verts and difference == 0:
        f_v = list(itertools.chain.from_iterable(verts))
        mesh.vertices.foreach_set('co', f_v)
        mesh.update()
    else:

        ''' get bmesh, write bmesh to obj, free bmesh'''
        bm = bmesh_from_pydata(verts, edges, faces, normal_update=node.calc_normals)
        if materials:
            for face, material in zip(bm.faces[:], materials):
                if material is not None:
                    face.material_index = material
        bm.to_mesh(sv_object.data)
        if node.randomize_vcol_islands:
            islands = find_islands_treemap(bm)
        bm.free()

        sv_object.hide_select = False

    if node.randomize_vcol_islands:
        set_vertices(sv_object, islands)

    if matrix:
        # matrix = matrix_sanitizer(matrix)
        if node.extended_matrix:
            sv_object.data.transform(matrix)
            sv_object.matrix_local = Matrix.Identity(4)
        else:
            sv_object.matrix_local = matrix
    else:
        sv_object.matrix_local = Matrix.Identity(4)


def make_bmesh_geometry_merged(node, obj_index, context, yielder_object):
    scene = context.scene
    collection = scene.collection
    meshes = bpy.data.meshes
    objects = bpy.data.objects
    name = f'{node.basedata_name}.{obj_index:04d}'

    if name in objects:
        sv_object = objects[name]
    else:
        temp_mesh = default_mesh(name)
        sv_object = objects.new(name, temp_mesh)
        collection.objects.link(sv_object)

    # book-keeping via ID-props!
    sv_object['idx'] = obj_index
    sv_object['madeby'] = node.name
    sv_object['basedata_name'] = node.basedata_name

    vert_count = 0
    big_verts = []
    big_edges = []
    big_faces = []
    big_materials = []

    for result in yielder_object:

        verts, topology = result
        edges, faces, materials, matrix = topology

        if matrix:
            # matrix = matrix_sanitizer(matrix)
            verts = [matrix @ Vector(v) for v in verts]

        big_verts.extend(verts)
        big_edges.extend([[a + vert_count, b + vert_count] for a, b in edges])
        big_faces.extend([[j + vert_count for j in f] for f in faces])
        big_materials.extend(materials)

        vert_count += len(verts)

    if node.fixed_verts and len(sv_object.data.vertices) == len(big_verts):
        mesh = sv_object.data
        f_v = list(itertools.chain.from_iterable(big_verts))
        mesh.vertices.foreach_set('co', f_v)
        mesh.update()
    else:
        ''' get bmesh, write bmesh to obj, free bmesh'''
        bm = bmesh_from_pydata(big_verts, big_edges, big_faces, normal_update=node.calc_normals)
        if materials:
            for face, material in zip(bm.faces[:], big_materials):
                if material is not None:
                    face.material_index = material
        bm.to_mesh(sv_object.data)
        bm.free()

    sv_object.hide_select = False
    sv_object.matrix_local = Matrix.Identity(4)


class SvMeshViewer(bpy.types.Node, SverchCustomTreeNode, SvObjHelper, BlenderObjects):
    """ bmv Generate Live geom """

    bl_idname = 'SvMeshViewer'
    bl_label = 'Mesh viewer'
    bl_icon = 'OUTLINER_OB_MESH'
    sv_icon = 'SV_BMESH_VIEWER'

    mesh_data: bpy.props.CollectionProperty(type=SvMeshData)

    grouping: BoolProperty(default=False, update=SvObjHelper.group_state_update_handler)
    merge: BoolProperty(default=False, update=updateNode)

    calc_normals: BoolProperty(default=False, update=updateNode)

    fixed_verts: BoolProperty(
        default=False,
        description="Use only with unchanging topology")

    autosmooth: BoolProperty(
        default=False,
        update=updateNode,
        description="This auto sets all faces to smooth shade")

    extended_matrix: BoolProperty(
        default=False,
        description='Allows mesh.transform(matrix) operation, quite fast!')

    randomize_vcol_islands: BoolProperty(
        default=False,
        description="experimental option to find islands in the outputmesh and colour them randomly")

    to3d: BoolProperty(default=False, update=updateNode)
    show_wireframe: BoolProperty(default=False, update=updateNode, name="Show Edges")

    def sv_init(self, context):
        self.sv_init_helper_basedata_name()

        self.inputs.new('SvVerticesSocket', 'vertices')
        self.inputs.new('SvStringsSocket', 'edges')
        self.inputs.new('SvStringsSocket', 'faces')
        self.inputs.new('SvStringsSocket', 'material_idx')
        self.inputs.new('SvMatrixSocket', 'matrix')

        self.outputs.new('SvObjectSocket', "Objects")

    def draw_buttons(self, context, layout):
        self.draw_live_and_outliner(context, layout)

        # additional UI options.
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "grouping", text="Group", toggle=True)
        row.prop(self, "merge", text="Merge", toggle=True)

        self.draw_object_buttons(context, layout)

    def draw_buttons_ext(self, context, layout):
        # self.draw_buttons(context, layout)
        self.draw_ext_object_buttons(context, layout)

        col = layout.column(align=True)
        box = col.box()
        if box:
            box.label(text='Beta options')
            box.prop(self, 'extended_matrix', text='Extended Matrix')
            box.prop(self, 'fixed_verts', text='Fixed vert count')
            box.prop(self, 'autosmooth', text='smooth shade')
            box.prop(self, 'calc_normals', text='calculate normals')
            box.prop(self, 'layer_choice', text='layer')
            box.prop(self, 'randomize_vcol_islands', text='randomize vcol islands')
            box.prop(self, 'show_wireframe')
        col.prop(self, 'to3d')

    def draw_label(self):
        return f"MeV {self.basedata_name}"

    @property
    def draw_3dpanel(self):
        return self.to3d

    def draw_buttons_3dpanel(self, layout):
        row = layout.row(align=True)
        # row.alert = warning
        row.prop(self, 'basedata_name', text='')
        row.prop_search(self, 'material_pointer', bpy.data, 'materials', text='', icon='MATERIAL_DATA')
        # row.operator('node.sv_callback_bmesh_viewer',text='',icon='RESTRICT_SELECT_OFF')

    def get_geometry_from_sockets(self):

        def get(socket_name):
            return self.inputs[socket_name].sv_get(default=[])

        mverts = get('vertices')
        medges = get('edges')
        mfaces = get('faces')
        if 'material_idx' in self.inputs:
            materials = get('material_idx')
        else:
            materials = []
        mmtrix = get('matrix')
        return mverts, medges, mfaces, materials, mmtrix

    def get_structure(self, stype, sindex):
        if not stype:
            return []

        try:
            j = stype[sindex]
        except IndexError:
            j = []
        finally:
            return j

    def process(self):

        if not self.activate:
            return

        verts = self.inputs['vertices'].sv_get(deepcopy=False, default=[])
        edges = self.inputs['edges'].sv_get(deepcopy=False, default=cycle([None]))
        faces = self.inputs['faces'].sv_get(deepcopy=False, default=cycle([None]))
        mat_indexes = self.inputs['material_idx'].sv_get(deepcopy=False, default=[])
        matrices = self.inputs['matrix'].sv_get(deepcopy=False, default=[])

        objects_number = max([len(verts), len(matrices)])  # todo if merged

        correct_collection_length(self.mesh_data, objects_number)
        [me_data.regenerate_mesh(self.basedata_name, v, e, f) for me_data, v, e, f in
            zip(self.mesh_data, verts, edges, faces)]
        self.regenerate_objects([self.basedata_name], [d.mesh for d in self.mesh_data])

        self.outputs['Objects'].sv_set([obj_data.obj for obj_data in self.object_data])

    def set_autosmooth(self, objs):
        if not self.autosmooth:
            return

        for obj in objs:
            mesh = obj.data
            smooth_states = [True] * len(mesh.polygons)
            mesh.polygons.foreach_set('use_smooth', smooth_states)
            mesh.update()

    def set_wireframe_visibility(self, objs):
        # this will only update the obj if there is a state change.
        for obj in objs:
            if obj.show_wire != self.show_wireframe:
                obj.show_wire = self.show_wireframe

    def add_material(self):

        mat = bpy.data.materials.new('sv_material')
        mat.use_nodes = True
        mat.use_fake_user = True

        nodes = mat.node_tree.nodes
        self.material_pointer = mat

        if bpy.context.scene.render.engine == 'CYCLES':
            # add attr node to the left of diffuse BSDF + connect it
            diffuse_node = nodes['Diffuse BSDF']
            attr_node = nodes.new('ShaderNodeAttribute')
            attr_node.location = (-170, 300)
            attr_node.attribute_name = 'SvCol'

            links = mat.node_tree.links
            links.new(attr_node.outputs[0], diffuse_node.inputs[0])

    def sv_copy(self, other):
        with self.sv_throttle_tree_update():
            print('copying bmesh node')
            dname = get_random_init_v3()
            self.basedata_name = dname


def register():
    bpy.utils.register_class(SvMeshViewer)


def unregister():
    bpy.utils.unregister_class(SvMeshViewer)
