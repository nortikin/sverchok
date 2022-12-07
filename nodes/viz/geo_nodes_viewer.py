# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from itertools import cycle
from typing import Optional

import bpy
from bpy.props import StringProperty
from sverchok.data_structure import fixed_iter

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.handle_blender_data import BlModifier, BlSocket, correct_collection_length, BlTree
from sverchok.utils.nodes_mixins.generating_objects import SvViewerLightNode, SvMeshData, SearchNode


class SvUpdateNodeInterface(SearchNode, bpy.types.Operator):
    """Refresh the node sockets"""
    bl_idname = 'node.sv_update_node_interface'
    bl_label = 'Update node sockets'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        self.node.generate_sockets(context)
        return {'FINISHED'}


class SvAddNewGNTree(SearchNode, bpy.types.Operator):
    """Create and add new Geometry Nodes tree"""
    bl_idname = 'node.sv_add_new_gn_tree'
    bl_label = 'Add New GN Tree'
    bl_options = {'INTERNAL'}

    gn_name: StringProperty()

    def execute(self, context):
        tree = bpy.data.node_groups.new(self.gn_name, 'GeometryNodeTree')
        in_ = tree.nodes.new("NodeGroupInput")
        out = tree.nodes.new("NodeGroupOutput")
        out.location = (500, 0)
        in_s = out.inputs.new('NodeSocketGeometry', 'Geometry')
        tree.links.new(in_s, in_.outputs[0])
        self.node.gn_tree = tree
        return {'FINISHED'}

    def invoke(self, context, event):
        if hasattr(context, 'node'):
            self._node = context.node
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'gn_name', text='Tree name')


class SvEditGNTree(SearchNode, bpy.types.Operator):
    """Create and add new Geometry Nodes tree"""
    bl_idname = 'node.sv_edit_gn_tree'
    bl_label = 'Edit GN Tree'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        ng_tree = self.node.gn_tree
        editor = context.space_data
        editor.tree_type = 'GeometryNodeTree'
        bpy.context.space_data.pin = True
        editor.node_tree = ng_tree
        ng_tree['sv_tree'] = self.node.id_data
        return {'FINISHED'}


class SvExitGNTree(bpy.types.Operator):
    """Create and add new Geometry Nodes tree"""
    bl_idname = 'node.sv_exit_gn_tree'
    bl_label = 'Exit GN Tree'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        editor = context.space_data
        gn_tree = editor.node_tree
        editor.tree_type = 'SverchCustomTreeType'
        editor.node_tree = gn_tree['sv_tree']
        del gn_tree['sv_tree']
        return {'FINISHED'}


class SvGeoNodesViewerNode(
        SvViewerLightNode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: modifiers
    Tooltip:
    """
    bl_idname = 'SvGeoNodesViewerNode'
    bl_label = 'Geo Nodes Viewer'
    bl_icon = 'GEOMETRY_NODES' if bpy.app.version >= (3, 3) else 'NODETREE'
    sv_icon = 'SV_BETA'

    def generate_sockets(self, context):
        # remove all extra sockets
        if not self.gn_tree:
            for sv_s in list(self.inputs)[:2:-1]:
                self.inputs.remove(sv_s)
            self.process_node(context)
            return

        # remove sockets which are not presented in the modifier
        gn_socks = {s.identifier for s in self.gn_tree.inputs[1:]}
        for sv_s in self.inputs[3:]:
            if sv_s.identifier not in gn_socks:
                self.inputs.remove(sv_s)

        # add new sockets
        sv_socks = {s.identifier: i
                    for i, s in enumerate(self.inputs[3:], start=3)}
        for gn_s in self.gn_tree.inputs[1:]:
            if gn_s.identifier in sv_socks:
                continue
            bl_s = BlSocket(gn_s)
            sv_s = self.inputs.new(bl_s.sverchok_type, '', identifier=gn_s.identifier)
            sv_socks[sv_s.identifier] = len(self.inputs)-1

        # fix existing sockets
        for gn_s in self.gn_tree.inputs[1:]:
            sv_s = self.inputs[sv_socks[gn_s.identifier]]
            bl_s = BlSocket(gn_s)
            if sv_s.bl_idname != (s_type := bl_s.sverchok_type):
                sv_s = sv_s.replace_socket(s_type)
            bl_s.copy_properties(sv_s)
            if hasattr(sv_s, 'show_domain'):
                sv_s.show_domain = True

        # fix socket positions
        for new_pos, gn_s in enumerate(self.gn_tree.inputs[1:], start=3):
            if current_pos := sv_socks.get(gn_s.identifier, 0):
                self.inputs.move(current_pos, new_pos)
                sv_socks = {s.identifier: i for i, s
                            in enumerate(self.inputs[3:], start=3)}

        self.process_node(context)

    gn_tree: bpy.props.PointerProperty(
        type=bpy.types.NodeTree,
        poll=lambda s, t: t.type == 'GEOMETRY',  # https://developer.blender.org/T97879
        update=generate_sockets,
        description="Geometry nodes tree",
    )

    mesh_data: bpy.props.CollectionProperty(type=SvMeshData, options={'SKIP_SAVE'})
    fast_mesh_update: bpy.props.BoolProperty(
        default=True,
        update=lambda s, c: s.process_node(c),
        description="Usually should be enabled. If some glitches with"
                    " mesh update, switch it off")

    def draw_gn_tree_name(self, layout):
        row = layout.row(align=True)
        row.prop(self, 'gn_tree', text='')
        if self.gn_tree:
            op = row.operator(SvUpdateNodeInterface.bl_idname, text='',
                              icon='FILE_REFRESH')
            op.node_name = self.name
            op.tree_name = self.id_data.name
            op = row.operator(SvEditGNTree.bl_idname, text='', icon='FILE_PARENT')
            op.node_name = self.name
            op.tree_name = self.id_data.name
        else:
            op = row.operator(SvAddNewGNTree.bl_idname, text='', icon='ADD')
            op.node_name = self.name
            op.tree_name = self.id_data.name

    def sv_draw_buttons(self, context, layout):
        self.draw_viewer_properties(layout)
        self.draw_gn_tree_name(layout)

    def draw_buttons_fly(self, layout):
        super().draw_buttons_fly(layout)
        self.draw_gn_tree_name(layout)

        col = layout.column()
        col.prop(self, 'fast_mesh_update')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.init_viewer()

    def sv_copy(self, other):
        super().sv_copy(other)
        self.mesh_data.clear()

    def sv_free(self):
        for data in self.mesh_data:
            data.remove_data()
        super().sv_free()

    def bake(self):
        for obj_d, me_d in zip(self.object_data, self.mesh_data):
            obj = obj_d.copy()
            me = me_d.copy()
            obj.data = me

    def process(self):
        if not self.is_active:
            return

        verts = self.inputs['Vertices'].sv_get(deepcopy=False, default=[])
        edges = self.inputs['Edges'].sv_get(deepcopy=False, default=[[]])
        faces = self.inputs['Faces'].sv_get(deepcopy=False, default=[[]])

        obj_num = len(verts)

        # regenerate mesh data blocks
        correct_collection_length(self.mesh_data, obj_num)
        create_mesh_data = zip(self.mesh_data, cycle(verts), cycle(edges), cycle(faces))
        for me_data, v, e, f in create_mesh_data:
            me_data.regenerate_mesh(self.base_data_name, v, e, f, make_changes_test=self.fast_mesh_update)

        # regenerate object data blocks
        # tree.sv_show triggers scene update so the tree attribute also should
        # be taken into account
        self.regenerate_objects([self.base_data_name],
                                [d.mesh for d in self.mesh_data],
                                to_show=[self.id_data.sv_show and self.show_objects])
        objs = [obj_data.obj for obj_data in self.object_data]
        self.outputs[0].sv_set(objs)

        props = [s.sv_get(deepcopy=False, default=[]) for s in self.inputs[3:]]
        props = [fixed_iter(sock_data, obj_num, None) for sock_data in props]
        props = zip(*props) if props else fixed_iter([], obj_num, [])

        gn_tree = BlTree(self.gn_tree) if self.gn_tree else None
        gn_inputs = gn_tree and {s.identifier: s for s in self.gn_tree.inputs[1:]}

        if self.gn_tree is None:
            for obj in objs:
                mod = self.get_modifier(obj, create=False)
                if mod is not None:
                    mod.remove()
        else:
            for obj, prop in zip(objs, props):
                mod = self.get_modifier(obj)
                if mod.node_group != self.gn_tree:
                    mod.node_group = self.gn_tree
                mod.gn_tree = gn_tree
                for sv_s, s_data in zip(self.inputs[3:], prop):
                    if not (gn_s := gn_inputs.get(sv_s.identifier)):
                        continue  # GN API was changed but the node was not updated
                    domain = sv_s.domain if hasattr(sv_s, 'domain') else 'POINT'
                    mod.set_tree_data(gn_s.identifier, s_data, domain)
                obj.data.update()

    def get_modifier(self, obj, create=True) -> Optional[BlModifier]:
        """Whenever geometry tree updates its interface, the modifier clears
        its all Custom properties, so they can't be used to keep node_id"""
        for mod in obj.modifiers:
            if mod.name == "SvGeoNodesViewer":
                break
        else:
            if create:
                mod = obj.modifiers.new("SvGeoNodesViewer", 'NODES')
                mod.node_group = self.gn_tree
            else:
                mod = None
        return mod and BlModifier(mod)


def draw_exit_edit_gn_tree(self, context):
    if tree := getattr(context.space_data, 'node_tree'):
        if 'sv_tree' in tree:
            self.layout.operator(
                SvExitGNTree.bl_idname, text='Sverchok', icon='FILE_PARENT')


classes = [
    SvGeoNodesViewerNode,
    SvUpdateNodeInterface,
    SvAddNewGNTree,
    SvEditGNTree,
    SvExitGNTree,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.NODE_HT_header.append(draw_exit_edit_gn_tree)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
