# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy

from sverchok.utils.logging import error
from sverchok.utils.handle_blender_data import BlTrees


imported_dummys = {}  # dummy node classes
dummy_nodes_dict = {}  # bl_idnames of nodes which was not registered due some dependencies missing


def add_dummy(bl_id, name, dependency):
    """
    Usage example:

    from sverchok.dependencies import FreeCAD
    from sverchok.utils.dummy_nodes import add_dummy

    if FreeCAD is None:
                     bl_idname        bl_label     dependency
        add_dummy('SvBoxSolidNode', 'Box (Solid)', 'FreeCAD')
    else:
        class SvBoxSolidNode(...):
            ... ....

    this will create a dummy node if needed
    """
    dummy_nodes_dict[bl_id] = [name, dependency]


class SvDummyNode:
    """This mixin is used to in nodes that have external dependencies that are not loaded."""
    bl_label = 'Dummy Node'
    bl_idname = 'SvDummyNode'

    def draw_buttons(self, context, layout):
        box = layout.box()
        box.label(text=self.missing_dependency + " module")
        box.label(text="not found. Check ")
        box.label(text="extra-nodes in preferences")


def is_dependent(bl_id):
    """True if the class was not registered due some dependencies missing"""
    return bl_id in dummy_nodes_dict


def mark_dummy(node):
    """Create frame node around the node with Missing dependencies label"""
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


def create_dummy_class(bl_id):
    """Create a dummy node class with given bl_idname"""
    from sverchok.node_tree import SverchCustomTreeNode
    label, dependency_name = dummy_nodes_dict[bl_id]
    return type(
        bl_id,
        (bpy.types.Node, SverchCustomTreeNode, SvDummyNode),
        {
            'bl_idname': bl_id,
            'bl_label': label,
            "missing_dependency": dependency_name,
        }
    )


def register_dummy(bl_id):
    """Register dummy class if was not registered yet"""
    if bl_id in dummy_nodes_dict:
        if bl_id not in imported_dummys:
            cls = create_dummy_class(bl_id)
            bpy.utils.register_class(cls)
            imported_dummys[bl_id] = cls
    else:
        raise LookupError("Cannot find {} among dummy nodes".format(bl_id))


def unregister_dummy(bl_id):
    cls = imported_dummys.get(bl_id)
    if cls:
        bpy.utils.unregister_class(cls)
        del imported_dummys[bl_id]


def mark_all():
    """Add frames with deprecated label to all deprecated nodes if necessary"""
    for node in (n for t in BlTrees().sv_trees for n in t.nodes):
        if node.bl_idname in dummy_nodes_dict:
            mark_dummy(node)


def register_all():
    """Register all dummies"""
    for bl_idname in dummy_nodes_dict:
        try:
            register_dummy(bl_idname)
        except Exception as e:
            error(e)


def register():
    import sverchok
    # this part is called only when Sverchok is reloading
    # we can't say to which class a node with unregistered class is belonging without registering it
    if sverchok.reload_event:
        register_all()


def unregister():
    for cls in imported_dummys.values():
        bpy.utils.unregister_class(cls)
