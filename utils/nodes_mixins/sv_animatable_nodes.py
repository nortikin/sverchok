# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from bpy.props import BoolProperty


# pylint: disable=c0111
# pylint: disable=c0103


class SvAnimatableNode():
    '''
    This mixin is used to add is_animatable property to the node.
    This property is used on frame change to determine which nodes should be updated
    
    To allow the user to control it just add layout.prop(self, 'is_animatable')
    probably in the draw_buttons_ext function
    '''
    is_animatable = BoolProperty(
        name="Animate Node",
        description="Update Node on frame change",
        default=True
    )
