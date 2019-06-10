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

import json

import bpy
from bpy.utils import register_class, unregister_class
from bpy.props import StringProperty, BoolProperty, FloatProperty


class Sv3DPanelPropsExporter(bpy.types.Operator):
    """Export current tree settings to .JSON file. (int, float, lists, bmesh)"""
    bl_idname = "node.tree_props_exporter"
    bl_label = "Export settings"

    target_node = bpy.props.StringProperty(name="Target node ID")
    filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob = StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context):
        if not self.filepath.endswith('.json') and not self.filepath.endswith('.JSON'):
            self.filepath += '.json'

        with open(self.filepath, 'w') as file:

            export = {'node': self.target_node, 'data': []}

            # Scan all node groups...
            for tree in bpy.data.node_groups:

                # ...and searching for target node
                if tree.name == self.target_node:
                    for item in tree.Sv3DProps:

                        no = item.node_name
                        prop = item.prop_name
                        node = tree.nodes[no]
                        row = {'type': node.bl_idname, 'prop': prop, 'id': no}
                        if node.label:
                            row['label'] = node.label

                        # Scalar
                        if node.bl_idname in {"IntegerNode", "FloatNode", "SvNumberNode"}:
                            row['value'] = getattr(node, prop, None)

                        # BMesh
                        elif node.bl_idname == "SvBmeshViewerNodeMK2":
                            row['value'] = getattr(node, prop, None)
                            row['material'] = node.material

                        # Lists
                        elif node.bl_idname == "SvListInputNode":
                            row['items'] = []
                            row['mode'] = node.mode
                            if node.mode == 'vector':
                                for i in range(node.v_int):
                                    row['items'].append([node.vector_list[i * 3 + j] for j in range(3)])
                            else:
                                for i in range(node.int_):
                                    row['items'].append(getattr(node, node.mode)[i])

                        # Color
                        elif node.bl_idname == "SvColorInputNode":
                            row['value'] = [c for c in getattr(node, prop, None)]

                        # Objects
                        elif node.bl_idname == "SvObjectsNodeMK3":
                            row['value'] = [pg.items()[0][1] for pg in node.object_names]

                        export['data'].append(row)

                    # print(json.dumps(export, ensure_ascii=False, indent=2))
                    file.write(json.dumps(export, ensure_ascii=False, indent=2))

        return {'FINISHED'}

    def invoke(self, context, event):
        # event.mouse_x
        # event.mouse_y
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class Sv3DPanelPropsImporter(bpy.types.Operator):
    """Import current tree settings from .JSON file"""
    bl_idname = "node.tree_props_importer"
    bl_label = "Import settings"

    target_node = bpy.props.StringProperty(name="Target node ID")
    filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob = StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context):
        with open(self.filepath, 'r') as file:
            imported = json.loads(file.read())
            for tree in bpy.data.node_groups:
                if tree.name == self.target_node:
                    for row in imported['data']:
                        node = tree.nodes[row['id']]

                        # Scalar
                        if node.bl_idname in {"IntegerNode", "FloatNode", "SvNumberNode", "SvBmeshViewerNodeMK2"}:
                            setattr(node, row['prop'], row['value'])
                            # BMesh
                            if node.bl_idname == "SvBmeshViewerNodeMK2":
                                node.material = row['material']

                        # Lists
                        elif node.bl_idname == "SvListInputNode":
                            for i in range(len(row['items'])):
                                if row['mode'] == 'vector':
                                    for j in range(3):
                                        getattr(node, row['prop'])[i * 3 + j] = row['items'][i][j]
                                else:
                                    getattr(node, row['mode'])[i] = row['items'][i]

                        # Color
                        elif node.bl_idname == "SvColorInputNode":
                            for i in range(4):
                                getattr(node, row['prop'])[i] = row['value'][i]

                        # Objects
                        elif node.bl_idname == "SvObjectsNodeMK3":
                            for obj_name in row['value']:
                                print('- ', obj_name)
                                # TODO: reassign objects

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


classes = [
    Sv3DPanelPropsExporter,
    Sv3DPanelPropsImporter,
]


def register():
    _ = [register_class(cls) for cls in classes]


def unregister():
    _ = [unregister_class(cls) for cls in classes[::-1]]
