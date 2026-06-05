# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import itertools
from collections import defaultdict

import bmesh
import bpy
from bpy.props import (BoolProperty, FloatProperty, IntProperty)

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.generating_objects import SvMeshData, SvViewerNode
from sverchok.data_structure import updateNode, fullList_np, numpy_full_list
from sverchok.utils.sv_obj_helper import SvObjHelper
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh


def process_mesh_into_features(skin_vertices, edge_keys, assume_unique=True):
    """
    be under no illusion that this function is an attempt at an optimized tip/junction finder.
    primarily it exists to test an assumption about foreach_set and obj.data.skin_verts edge keys.

        # this works for a edgenet mesh (polyline) that has no disjoint elements
        # but I think all it does it set the last vertex as the root.
        obj.data.skin_vertices[0].data.foreach_set('use_root', all_yes)

    disjoint elements each need 1 vertex set to root
    """

    # need a set of sorted keys
    if not assume_unique:
        try:
            edge_keys = set(edge_keys)
        except:
            # this will be slower..but it should catch most input
            edge_keys = set(tuple(sorted(key)) for key in edge_keys)
    else:
        edge_keys = set(edge_keys)

    # iterate and accumulate
    ndA = defaultdict(set)
    for key in edge_keys:
        lowest, highest = key
        ndA[lowest].add(highest)
        ndA[highest].add(lowest)

    ndB = defaultdict(set)
    ndC = {k: len(ndA[k]) for k in sorted(ndA.keys()) if len(ndA[k]) == 1 or len(ndA[k]) >= 3}
    for k, v in ndC.items():
        ndB[v].add(k)

    # in heavily branching input, there will be a lot of redundant use_root pushing.
    for k in sorted(ndB.keys()):
        for index in ndB[k]:
            skin_vertices[index].use_root = True
        pass
    return


def set_data_for_layer(bm, data, layer):
    for i in range(len(bm.verts)):
        bm.verts[i][data] = layer[i] or 0.1
    return


def shrink_geometry(bm, dist, layers):
    vlayers = bm.verts.layers
    made_layers = []
    for idx, layer in enumerate(layers):
        first_element = layer[0] or 0.2
        if isinstance(first_element, float):
            data_layer = vlayers.float.new('float_layer' + str(idx))

        made_layers.append(data_layer)
        bm.verts.ensure_lookup_table()
        set_data_for_layer(bm, data_layer, layer)

    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=dist)
    bm.verts.ensure_lookup_table()

    verts, edges, _ = pydata_from_bmesh(bm)
    data_out = [verts, edges]
    for layer_name in made_layers:
        data_out.append([bm.verts[i][layer_name] for i in range(len(bm.verts))])

    return data_out


def force_pydata(mesh, verts, edges):

    mesh.vertices.add(len(verts))
    f_v = list(itertools.chain.from_iterable(verts))
    mesh.vertices.foreach_set('co', f_v)
    mesh.update()

    mesh.edges.add(len(edges))
    f_e = list(itertools.chain.from_iterable(edges))
    mesh.edges.foreach_set('vertices', f_e)
    mesh.update(calc_edges=True)
    return

def analyze_mesh_islands_and_topology(obj):
    """
    За один проход собирает топологию меша без BMesh.
    Возвращает:
    - islands: список списков с ИНДЕКСАМИ рёбер для каждого острова.
    - vertex_neighbors_count: словарь {индекс_вершины: количество_соседей}.
    - junction_vertices: сет ИНДЕКСОВ вершин, у которых 3 и более соседа (развилки).
    """
    # 1. Сбор списка смежности и подсчет соседей за O(N)
    adj = {v.index: [] for v in obj.data.vertices}
    vertex_neighbors_count = {v.index: 0 for v in obj.data.vertices}
    
    for edge in obj.data.edges:
        u, v = edge.vertices
        idx = edge.index
        adj[u].append((v, idx))
        adj[v].append((u, idx))
        # Считаем количество смежных ребер для каждой вершины
        vertex_neighbors_count[u] += 1
        vertex_neighbors_count[v] += 1

    # Сразу выделяем вершины-развилки (junctions) для Skin Loose маркировки
    junction_vertices = {v_idx for v_idx, count in vertex_neighbors_count.items() if count >= 3}
        
    # 2. Поиск островов (BFS обход)
    visited_verts = [False] * len(obj.data.vertices)
    islands = []
    
    for start_v in range(len(obj.data.vertices)):
        if visited_verts[start_v]:
            continue
            
        island_edges = []
        seen_edges = set()
        queue = [start_v]
        visited_verts[start_v] = True
        
        while queue:
            curr_v = queue.pop(0)
            
            for neighbor_v, edge_idx in adj[curr_v]:
                if edge_idx not in seen_edges:
                    seen_edges.add(edge_idx)
                    island_edges.append(edge_idx)
                    
                if not visited_verts[neighbor_v]:
                    visited_verts[neighbor_v] = True
                    queue.append(neighbor_v)
                    
        if island_edges:
            islands.append(island_edges)
            
    return islands, vertex_neighbors_count, junction_vertices

def make_bmesh_geometry(node, context, geometry, idx, layers):
    collection = context.scene.collection
    meshes = bpy.data.meshes
    objects = bpy.data.objects
    verts, edges, matrix, _, _ = geometry

    name = f'{node.basedata_name}.{idx:04d}'

    if name in objects:
        obj = objects.get(name)
        node.clear_current_mesh(obj.data)
    else:
        # this is only executed once, upon the first run.
        mesh = meshes.new(name)
        obj = objects.new(name, mesh)
        collection.objects.link(obj)

    # at this point the mesh is always fresh and empty
    obj['idx'] = idx
    obj['basedata_name'] = node.basedata_name

    data_layers = None
    if node.distance_doubles > 0.0:
        bm = bmesh_from_pydata(verts, edges, [])
        verts, edges, *data_layers = shrink_geometry(bm, node.distance_doubles, layers)

    force_pydata(obj.data, verts, edges)
    obj.update_tag(refresh={'OBJECT', 'DATA'})

    if node.activate:

        if node.skin_modifier_name_ in obj.modifiers:
            sk = obj.modifiers[node.skin_modifier_name_]
            # obj.modifiers.remove(sk)
            if not obj.data.skin_vertices:
                # Create temp modifier if skin_vertices are not exists:
                tmp_index = 0
                tmp_name = f"skin_tmp_name_{tmp_index}"
                while (tmp_name in obj.modifiers):
                    tmp_name = f"skin_tmp_name_{tmp_index}"
                    tmp_index+=1
                    
                tmp = obj.modifiers.new(tmp_name, 'SKIN')
                # If skin_vertices layer not created
                if not obj.data.skin_vertices:
                    # try update view_layer
                    bpy.context.view_layer.update()
                if not obj.data.skin_vertices:
                    # Layer is not created.
                    raise Exception(f"\"{obj.name}\".data.skin_vertices are not created! (Try recreate in in Blender UI)")
                    pass
                obj.modifiers.remove(tmp)
        else:
            sk = obj.modifiers.new(type='SKIN', name=node.skin_modifier_name_)

        if node.subdiv_modifier_name in obj.modifiers:
            sd = obj.modifiers[node.subdiv_modifier_name]
            # obj.modifiers.remove(sd)
        else:
            sd = obj.modifiers.new(type='SUBSURF', name=node.subdiv_modifier_name)

        # sk = obj.modifiers.new(type='SKIN', name='sv_skin')
        sk.branch_smoothing = node.branch_smoothing
        sk.use_x_symmetry   = node.use_x_symmetry
        sk.use_y_symmetry   = node.use_y_symmetry
        sk.use_z_symmetry   = node.use_z_symmetry
        sk.use_smooth_shade = node.use_smooth_shade
        
        sd.show_viewport    = node.subdiv_modifier_show_vieweport
        sd.levels           = node.levels
        sd.render_levels    = node.render_levels

    node.push_custom_matrix_if_present(obj, matrix)

    return obj, data_layers

class SvSkinViewerNodeV28(SverchCustomTreeNode, SvViewerNode, bpy.types.Node, SvObjHelper):
    """
    Triggers: Output Skin Mesh
    Tooltip: Outputs Blender Edges + Skin Modifier + Subdivision Surface.\n\tIn: vertices, edges, matrix, radius x/y\n\tParams: base name, subdiv view/render, merge distance

    """
    bl_idname = 'SvSkinViewerNodeV28'
    bl_label = 'Skin Mesher'
    bl_icon = 'MOD_SKIN'
    sv_icon = 'SV_SKIN_MESHER'

    #skin_modifier_name_002 = "" # Старое имя
    
    def getSkinModifierName(self,):
        return self.skin_modifier_name_
    
    def setSkinModifierName(self, value):
        value = value.strip()
        self["skin_modifier_name"] = self.get("skin_modifier_name", "")
        if value:
            objs = self.get_children()
            for obj in objs:
                if self["skin_modifier_name"] in obj.modifiers:
                    sv = obj.modifiers[self["skin_modifier_name"]]
                    sv.name = value
                    self["skin_modifier_name"] = value
                pass
        pass
        self.skin_modifier_name_ = value
        self["skin_modifier_name"] = value
        return

    skin_modifier_name_: bpy.props.StringProperty(
        default = 'sv_skin',
        name = "Skin modifier name",
        description = "Skin modifier name in object Modofier property panel",
        update=updateNode,
    )

    skin_modifier_name: bpy.props.StringProperty(
        default = 'sv_skin',
        name = "Skin modifier name",
        description = "Skin modifier name in object Modofier property panel",
        get = getSkinModifierName,
        set = setSkinModifierName,
    )
    
    def getSubdivModifierName(self,):
        return self.subdiv_modifier_name_
    
    def setSubdivModifierName(self, value):
        value = value.strip()
        self["subdiv_modifier_name"] = self.get("subdiv_modifier_name", "")
        if value:
            objs = self.get_children()
            for obj in objs:
                if self["subdiv_modifier_name"] in obj.modifiers:
                    sv = obj.modifiers[self["subdiv_modifier_name"]]
                    sv.name = value
                    self["subdiv_modifier_name"] = value
                pass
        pass
        self.subdiv_modifier_name_   = value
        self["subdiv_modifier_name"] = value
        return

    subdiv_modifier_name_: bpy.props.StringProperty(
        default = 'sv_subdiv',
        name = "Subdiv modifier name",
        description = "Subdiv modifier name in object Modofier property panel",
        update=updateNode,
    )

    subdiv_modifier_name: bpy.props.StringProperty(
        default = 'sv_subdiv',
        name = "Subdiv modifier name",
        description = "Subdiv modifier name in object Modofier property panel",
        get = getSubdivModifierName,
        set = setSubdivModifierName,
    )

    general_radius_x: FloatProperty(
        name='Radius x',
        default=0.25,
        description='value used to uniformly set the radii of skin vertices x',
        min=0.0001, step=0.05,
        update=updateNode)

    general_radius_y: FloatProperty(
        name='Radius y',
        default=0.25,
        description='value used to uniformly set the radii of skin vertices y',
        min=0.0001, step=0.05,
        update=updateNode)

    levels: IntProperty(
        min=0,
        name="Levels Viewport",
        description="Number of subdivision to perform",
        default=1,
        max=3,
        update=updateNode,
    )
    render_levels: IntProperty(
        min=0,
        name="Render",
        description="Number of subdivision to perform when rendering",
        default=1,
        max=3,
        update=updateNode,
    )

    distance_doubles: FloatProperty(
        default=0.0, min=0.0,
        name='Doubles distance',
        description="removes coinciding verts, also aims to remove double radii data",
        update=updateNode)

    use_root: BoolProperty(
        default=True,
        name = "Mark Root",
        description = "Automaticatty find and mark root vertices",
        update=updateNode,
    )
    use_slow_root: BoolProperty(default=False, update=updateNode)

    subdiv_modifier_show_vieweport: BoolProperty(
        default=True,
        name = "Show Viewerport",
        description="Display Modifier in viewport",
        update=updateNode,
    )

    branch_smoothing : FloatProperty(
        default=0.0, min=0.0, max=1.0, precision=3,
        name='Branch Smoothing',
        description='Smooth complex geometry around branches',
        update=updateNode)
    use_x_symmetry : BoolProperty(
        name='Symmetry X',
        description='Avoiding making unsymmetrical quads across the X axis',
        default=True,
        update = updateNode,
    )
    use_y_symmetry : BoolProperty(
        name='Symmetry Y',
        description='Avoiding making unsymmetrical quads across the Y axis',
        default=False,
        update = updateNode,
    )
    use_z_symmetry : BoolProperty(
        name='Symmetry Z',
        description='Avoiding making unsymmetrical quads across the Z axis',
        default=False,
        update = updateNode,
    )
    use_smooth_shade : BoolProperty(
        name='Smooth shading',
        description='Output faces with smooth shading rather than flat shaded',
        default=False,
        update = updateNode,
    )


    def sv_init(self, context):
        self.init_viewer()
        self.sv_init_helper_basedata_name()

        self.inputs.new('SvVerticesSocket', 'vertices')
        self.inputs.new('SvStringsSocket', 'edges')
        self.inputs.new('SvMatrixSocket', 'matrix')
        self.inputs.new('SvStringsSocket', 'radii_x').prop_name = "general_radius_x"
        self.inputs.new('SvStringsSocket', 'radii_y').prop_name = "general_radius_y"


    def draw_buttons(self, context, layout):
        self.draw_live_and_outliner(context, layout)
        self.draw_object_buttons(context, layout)

        root = layout.column()

        root.use_property_decorate = False
        root.use_property_split = True
        col = root.box().column(align=True)
        col.label(text="Skin modifier properties:")
        r = col.row(align=False, heading='Realtime')
        r = col.row(align=True, heading='Symmetry')
        r.row(align=True).prop(self, 'branch_smoothing')
        r = col.row(align=False, heading='Symmetry')
        r.prop(self, 'use_x_symmetry', toggle=True, text='X')
        r.prop(self, 'use_y_symmetry', toggle=True, text='Y')
        r.prop(self, 'use_z_symmetry', toggle=True, text='Z')
        col.row(align=True).prop(self, 'use_smooth_shade')
        r = col.row(align=False, heading="Setting roots")
        r.prop(self, "use_root", toggle=True)
        r.prop(self, "use_slow_root", text="mark some", toggle=True)

        col = root.box().column(align=True)
        col.label(text="Subdiv modifier properties:")
        r1 = col.column(align=True)
        r2 = r1.row(align=False)
        r2.prop(self, 'subdiv_modifier_show_vieweport', icon='RESTRICT_VIEW_OFF' if self.subdiv_modifier_show_vieweport else 'RESTRICT_VIEW_ON', )
        r2.label(text='')
        r1.prop(self, 'levels', )
        r1.prop(self, 'render_levels', )
        col = root.box().column(align=True)
        col.prop(self, 'distance_doubles', )


    def draw_buttons_ext(self, context, layout):
        box = layout
        box.use_property_decorate = False
        box.use_property_split = True
        r = box.row(align=True, heading="Setting roots")
        r.prop(self, "use_root", text="mark all", toggle=True)
        r.prop(self, "use_slow_root", text="mark some", toggle=True)
        box.row(align=True).prop(self, 'branch_smoothing')
        r = box.row(align=True, heading='Symmetry')
        r.prop(self, 'use_x_symmetry', toggle=True, text='X')
        r.prop(self, 'use_y_symmetry', toggle=True, text='Y')
        r.prop(self, 'use_z_symmetry', toggle=True, text='Z')
        box.row(align=True).prop(self, 'use_smooth_shade')
        box.row(align=True).prop(self, 'skin_modifier_name')
        box.row(align=True).prop(self, 'subdiv_modifier_name')
        pass

    def get_geometry_from_sockets(self):
        i = self.inputs
        mverts = i['vertices'].sv_get(default=[])
        medges = i['edges'].sv_get(default=[])
        mmtrix = i['matrix'].sv_get(default=[None])
        mradiix = i['radii_x'].sv_get()
        mradiiy = i['radii_y'].sv_get()
        return mverts, medges, mmtrix, mradiix, mradiiy


    def process(self):
        if not self.activate:
            return
        
        # only interested in the first
        geometry_full = self.get_geometry_from_sockets()

        # pad all input to longest
        maxlen = max(*(map(len, geometry_full)))

        fullList_np(geometry_full[0], maxlen)
        fullList_np(geometry_full[1], maxlen)
        fullList_np(geometry_full[2], maxlen)
        fullList_np(geometry_full[3], maxlen)
        fullList_np(geometry_full[4], maxlen)

        catch_idx = 0
        for idx, (geometry) in enumerate(zip(*geometry_full)):
            catch_idx = idx
            self.unit_generator(idx, geometry)

        self.remove_non_updated_objects(catch_idx)
        self.set_corresponding_materials()

        objs = self.get_children()
        self.outputs['Objects'].sv_set(objs)
        return


    def unit_generator(self, idx, geometry):
        verts, _, _, radiix, radiiy = geometry
        ntimes = len(verts)

        radiix = numpy_full_list(radiix, ntimes)
        radiiy = numpy_full_list(radiiy, ntimes)
        radiuses = [radiix, radiiy]

        obj, data_layers = make_bmesh_geometry(self, bpy.context, geometry, idx, radiuses)

        if data_layers and self.distance_doubles > 0.0:
            # This sets the modified geometry with radius x and radius y.
            f_r = list(itertools.chain(*zip(data_layers[0], data_layers[1])))
            f_r = [abs(f) for f in f_r]
            obj.data.skin_vertices[0].data.foreach_set('radius', f_r)
            all_yes = list(itertools.repeat(True, len(obj.data.vertices)))
            obj.data.skin_vertices[0].data.foreach_set('use_root', all_yes)

        elif len(radiix) == len(verts):
            f_r = list(itertools.chain(*zip(radiix, radiiy)))
            f_r = [abs(f) for f in f_r]
            obj.data.skin_vertices[0].data.foreach_set('radius', f_r)

        if self.use_root:
            # set all to root
            #all_yes = list(itertools.repeat(True, ntimes))
            all_False = list(itertools.repeat(False, ntimes))
            #obj.data.skin_vertices[0].data.foreach_set('use_root', all_yes)
            #obj.data.skin_vertices[0].data.foreach_set('use_loose', all_False)
            
            # # Автоматически находим сложные развилки и маркируем их как Loose
            # skin_verts = obj.data.skin_vertices[0].data
            # # 1. Vertices counter
            # edge_counts = {v.index: 0 for v in obj.data.vertices}

            # # 2. Fill edges counter for every vertices
            # for edge in obj.data.edges:
            #     edge_counts[edge.vertices[0]] += 1
            #     edge_counts[edge.vertices[1]] += 1

            # for vert in obj.data.vertices:
            #     skin_verts[vert.index].use_root = False
            #     skin_verts[vert.index].use_loose = False
            
            # is_edges_count_3 = False
            # for vert in obj.data.vertices:
            #     # find vertices with 3 or more edges then mark it as root
            #     edges_count = edge_counts[vert.index]
                
            #     if edges_count >= 3 or edges_count==1:
            #         skin_verts[vert.index].use_root = True
            #         is_edges_count_3 = True
            #     pass
            # if is_edges_count_3==False and len(obj.data.vertices)>0:
            #     skin_verts[0].use_root = True

            # obj.data.update()
            # #obj.update_tag()

            # Запускаем комплексный анализ
            islands, neighbors_count, junctions = analyze_mesh_islands_and_topology(obj)

            skin_verts = obj.data.skin_vertices[0].data

            # Шаг 1: Сброс
            for sv in skin_verts:
                sv.use_root = False
                sv.use_loose = False

            # Шаг 2: Маркируем ВСЕ развилки как Loose (для сглаживания формы) 
            # и одновременно как Root (для выравнивания петель и сетки)
            # for j_idx in junctions:
            #     skin_verts[j_idx].use_root = True  # Возвращаем корни на развилки!

            # Шаг 3: Проверяем острова. 
            # Если на каком-то острове вообще нет развилок (например, это просто одиночное кольцо или линия),
            # ему всё равно жизненно необходим хотя бы один Root, иначе он пропадет.
            for edge_indices in islands:
                # Проверяем, есть ли уже корень внутри этого острова
                has_root = False
                for e_idx in edge_indices:
                    u, v = obj.data.edges[e_idx].vertices
                    if skin_verts[u].use_root or skin_verts[v].use_root:
                        has_root = True
                        break
                    pass
                        
                # Если на острове нет корней, то найти один junction и установить его:
                if not has_root:
                    # first_edge = obj.data.edges[edge_indices[0]]
                    # fallback_root = first_edge.vertices[0]
                    # skin_verts[fallback_root].use_root = True
                    # Найти junction и добавить один корень:
                    has_root = False
                    for e_idx in edge_indices:
                        u, v = obj.data.edges[e_idx].vertices
                        if u in junctions:
                           skin_verts[u].use_root = True
                           has_root = True
                           break
                        if v in junctions:
                           skin_verts[v].use_root = True
                           has_root = True
                           break
                        pass
                    pass

                if not has_root:
                    # Назначить вершине в первом индексе:
                    first_edge = obj.data.edges[edge_indices[0]]
                    fallback_root = first_edge.vertices[0]
                    skin_verts[fallback_root].use_root = True
                    pass

            # Финальное обновление меша в Blender
            obj.data.update()

        elif self.use_slow_root:
            process_mesh_into_features(obj.data.skin_vertices[0].data, obj.data.edge_keys)


    def flip_roots_or_junctions_only(self, data):
        pass

    def draw_label(self):
        return f"{SvSkinViewerNodeV28.bl_label} ({self.basedata_name})"

def register():
    bpy.utils.register_class(SvSkinViewerNodeV28)

def unregister():
    bpy.utils.unregister_class(SvSkinViewerNodeV28)
