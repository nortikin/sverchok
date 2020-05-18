# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


"""
This modules keeps base classes for Sverchok nodes
Import this module only with `import` operator
"""


class OutputNode:
    # Ust it for all nodes which should show something for users (except in 3d viewport)
    # or node is interacting with Blender data

    @property
    def is_active_output(self) -> bool:
        # it is need for understanding is it worth to evaluate a node tree
        # should return False if it is switched off
        raise NotImplementedError


class ViewportViewerNode:
    # It should be used for all nodes which are drawing something into 3D viewport

    @property
    def show_view_port(self) -> bool:
        # is a node drawing in viewport
        raise NotImplementedError

    @show_view_port.setter
    def show_view_port(self, to_show: bool):
        # the property should be abel to switch on/off drawing in viewport
        raise NotImplementedError
