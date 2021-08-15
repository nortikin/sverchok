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

import os
import ast


def get_old_nodes_list(path):
    for fp in os.listdir(path):
        if fp.endswith(".py") and not fp.startswith('__'):
            yield fp

class SvBlIdnameFinder(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.bl_idname = None

    def visit_ClassDef(self, node):
        for statement in node.body:
            if isinstance(statement, ast.Assign):
                if len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
                    prop_name = statement.targets[0].id
                    if prop_name == 'bl_idname':
                        self.bl_idname = statement.value

def get_sv_nodeclasses(path, old_node_file):
    collection = []
    file_path = os.path.join(path, old_node_file)
    with open(file_path, errors='replace') as file:
        
        node = ast.parse(file.read())
        classes = [n for n in node.body if isinstance(n, ast.ClassDef)]
        node_classes = []
        for c in classes:
            for k in c.bases:
                if hasattr(k, 'id') and k.id == 'SverchCustomTreeNode':
                    node_classes.append(c)

        for node_class in node_classes:
            finder = SvBlIdnameFinder()
            finder.visit(node_class)
            bl_idname = finder.bl_idname or node_class.name
            collection.append([bl_idname, old_node_file])

    return collection

def get_old_node_bl_idnames(path):
    bl_dict = {}
    for old_node_file in get_old_nodes_list(path):
        items = get_sv_nodeclasses(path, old_node_file)
        for bl_idname, file_name in items:
            bl_dict[bl_idname] = file_name[:-3]
    # print('old nodes dict:', len(bl_dict))
    # print(bl_dict)
    return bl_dict
