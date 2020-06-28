# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import os
import importlib
import inspect
import traceback

import bpy
from bpy.props import StringProperty


from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.sv_oldnodes_parser import get_old_node_bl_idnames
from sverchok.utils.logging import error, exception
from sverchok.utils.nodes_mixins.sv_dummy_nodes import SvDummyNode

imported_dummys = {}


dummy_nodes_dict = {
    'SvBoxSolidNode': ['Box (Solid)', 'FreeCAD'],
    'SvSphereSolidNode': ['Sphere (Solid)', 'FreeCAD'],
    'SvCylinderSolidNode': ['Cylinder (Solid)', 'FreeCAD'],
    'SvTransformSolidNode': ['Transform Solid', 'FreeCAD'],
    'SvChamferSolidNode': ['Chamfer Solid', 'FreeCAD'],
    'SvFilletSolidNode': ['Fillet Solid', 'FreeCAD'],
    'SvSolidBooleanNode': ['Solid Boolean', 'FreeCAD'],
    'SvMeshToSolidNode': ['Mesh to Solid', 'FreeCAD'],
    'SvSolidToMeshNode': ['Solid to Mesh', 'FreeCAD'],
    }



class SvDummyNode():
    '''
    This mixin is used to in nodes that have external dependencies that are not loaded.

    '''
    bl_label = 'Dummy Node'
    bl_idname = 'SvDummyNode'

    def draw_buttons(self, context, layout):
        box = layout.box()
        box.label(text=self.missing_dependecy+" module")
        box.label(text="not found. Check ")
        box.label(text="extra-nodes in preferences")

def is_dependent(bl_id):
    return bl_id in dummy_nodes_dict

def is_dummy(node):
    '''
    Check if node or node.bl_idname is among
    the old nodes
    '''
    if isinstance(node, bpy.types.Node):
        return hasattr(node, 'missing_dependecy')
    else:
        return False

def scan_for_dummy(ng):
    nodes = [n for n in ng.nodes if is_dummy(n)]
    for node in nodes:
        mark_dummy(node)

def mark_dummy(node):
    if node.parent and node.parent.label == "Missing dependencies!":
        return
    ng = node.id_data
    frame = ng.nodes.new("NodeFrame")
    if node.parent:
        frame.parent = node.parent
    node.parent = frame
    frame.label = "Missing dependencies!"
    frame.use_custom_color = True
    frame.color = (.8, 0, 0)
    frame.shrink = True

def reload_dummy(ng=False):
    print("Reloading dummy")
    if ng:
        load_dummy(ng)
    else:
        for ng in bpy.data.node_groups:

            load_dummy(ng)

def create_dummy_class(bl_id):
    node = dummy_nodes_dict[bl_id]
    cls = type(bl_id,
              (bpy.types.Node, SverchCustomTreeNode, SvDummyNode),
              {'bl_idname': bl_id,
              'bl_label': node[0],
              # "missing_dependecy": StringProperty(name="Missing Dependency", default=node[1]),
              "missing_dependecy":node[1],
              })
    # cls['missing_dependecy'].default = node[1]
    return cls
def load_dummy(ng):

    not_reged_nodes = list(n for n in ng.nodes if not n.is_registered_node_type())
    if not_reged_nodes:
        for bl_id in dummy_nodes_dict:
            register_dummy(bl_id)
            nodes = [n for n in ng.nodes if n.bl_idname == bl_id]
            if nodes:
                for node in nodes:
                    mark_dummy(node)
                not_reged_nodes = list(n for n in ng.nodes if not n.is_registered_node_type())
                node_count = len(not_reged_nodes)
                print(f"Loaded {bl_id}. {node_count} nodes are left unregistered.")
                if node_count == 0:
                    return
            else: # didn't help remove
                unregister_dummy(bl_id)


def register_dummy(bl_id):

    if bl_id in dummy_nodes_dict:

        if bl_id not in imported_dummys:
            cls = create_dummy_class(bl_id)
            bpy.utils.register_class(cls)
            imported_dummys[bl_id] = cls
            return cls
        else:
            return imported_dummys[bl_id]
    error("Cannot find {} among old nodes".format(bl_id))
    return None

def unregister_dummy(bl_id):
    global imported_dummys
    cls = imported_dummys.get(bl_id)
    if cls:
        #print("Unloaded old node type {}".format(bl_id))
        bpy.utils.unregister_class(cls)

        del imported_dummys[bl_id]

def unregister():
    global imported_dummys
    print(imported_dummys)
    for cls in imported_dummys.values():
        bpy.utils.unregister_class(cls)
    imported_dummys = {}
