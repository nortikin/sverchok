# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from bpy.props import BoolProperty
from sverchok.data_structure import updateNode

# pylint: disable=c0111
# pylint: disable=c0103


class SvAnimatableNode():
    '''
    This mixin is used to add is_animatable property to the node.
    This property is used on frame change to determine which nodes should be updated
    The node file will need to have this code line:

    from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode

    And the node class will need to inherit this class.
    
    To allow the user to control it just add in draw buttons function:
        self.animatable_buttons(layout, icon_only=True)
    or/and in the draw_buttons_ext function
        self.animatable_buttons(layout)

    '''
    is_animatable = BoolProperty(
        name="Animate Node",
        description="Update Node on frame change",
        default=True
    )
    
    def refresh_node(self, context):
        if self.refresh:
            self.refresh = False
            updateNode(self, context)

    refresh = BoolProperty(
        name="Update Node",
        description="Update Node",
        default=False,
        update=refresh_node
    )
    
    def animatable_buttons(self, layout, icon_only=False):
        row = layout.row(align=True)
        row.prop(self, 'is_animatable', icon='ANIM', icon_only=icon_only)
        row.prop(self, 'refresh', icon='FILE_REFRESH', icon_only=icon_only)
