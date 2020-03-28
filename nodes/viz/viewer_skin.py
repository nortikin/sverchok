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


def set_data_for_layer(bm, data, layer):
    for i in range(len(bm.verts)):
        bm.verts[i][data] = layer[i] or 0.1


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
        verts, edges, _, *data_layers = shrink_geometry(bm, node.distance_doubles, layers)

    force_pydata(obj.data, verts, edges)
    obj.update_tag(refresh={'OBJECT', 'DATA'})

    if node.activate:

        if 'sv_skin' in obj.modifiers:
            sk = obj.modifiers['sv_skin']
            obj.modifiers.remove(sk)

        if 'sv_subsurf' in obj.modifiers:
            sd = obj.modifiers['sv_subsurf']
            obj.modifiers.remove(sd)

        _ = obj.modifiers.new(type='SKIN', name='sv_skin')
        b = obj.modifiers.new(type='SUBSURF', name='sv_subsurf')
        b.levels = node.levels
        b.render_levels = node.render_levels

    node.push_custom_matrix_if_present(obj, matrix)

    return obj, data_layers


class SvSkinViewerNodeV28(bpy.types.Node, SverchCustomTreeNode, SvObjHelper):
    """
    Triggers: Output Skin Mesh
    Tooltip: Outputs Blender Edges + Skin Modifier + Subdivision Surface

    """
    bl_idname = 'SvSkinViewerNodeV28'
    bl_label = 'Skin Mesher'
    bl_icon = 'MOD_SKIN'
    sv_icon = 'SV_SKIN_MESHER'

    general_radius_x: FloatProperty(
        name='general_radius_x',
        default=0.25,
        description='value used to uniformly set the radii of skin vertices x',
        min=0.0001, step=0.05,
        update=updateNode)

    general_radius_y: FloatProperty(
        name='general_radius_y',
        default=0.25,
        description='value used to uniformly set the radii of skin vertices y',
        min=0.0001, step=0.05,
        update=updateNode)

    levels: IntProperty(min=0, default=1, max=3, update=updateNode)
    render_levels: IntProperty(min=0, default=1, max=3, update=updateNode)

    distance_doubles: FloatProperty(
        default=0.0, min=0.0,
        name='doubles distance',
        description="removes coinciding verts, also aims to remove double radii data",
        update=updateNode)

    use_root: BoolProperty(default=True, update=updateNode)
    use_slow_root: BoolProperty(default=False, update=updateNode)


    def sv_init(self, context):
        self.sv_init_helper_basedata_name()

        self.inputs.new('SvVerticesSocket', 'vertices')
        self.inputs.new('SvStringsSocket', 'edges')
        self.inputs.new('SvMatrixSocket', 'matrix')
        self.inputs.new('SvStringsSocket', 'radii_x').prop_name = "general_radius_x"
        self.inputs.new('SvStringsSocket', 'radii_y').prop_name = "general_radius_y"


    def draw_buttons(self, context, layout):
        self.draw_live_and_outliner(context, layout)
        self.draw_object_buttons(context, layout)

        r1 = layout.column(align=True)
        r1.prop(self, 'levels', text="div View")
        r1.prop(self, 'render_levels', text="div Render")
        r1.prop(self, 'distance_doubles', text='doubles distance')


    def draw_buttons_ext(self, context, layout):
        k = layout.box()
        r = k.row(align=True)
        r.label(text="setting roots")
        r = k.row(align=True)
        r.prop(self, "use_root", text="mark all", toggle=True)
        r.prop(self, "use_slow_root", text="mark some", toggle=True)


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
            all_yes = list(itertools.repeat(True, ntimes))
            obj.data.skin_vertices[0].data.foreach_set('use_root', all_yes)
        elif self.use_slow_root:
            process_mesh_into_features(obj.data.skin_vertices[0].data, obj.data.edge_keys)


    def flip_roots_or_junctions_only(self, data):
        pass

    def draw_label(self):
        return f"SK {self.basedata_name}"

def register():
    bpy.utils.register_class(SvSkinViewerNodeV28)

def unregister():
    bpy.utils.unregister_class(SvSkinViewerNodeV28)
