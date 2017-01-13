# -*- coding: utf-8 -*-
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

import time
import math

import bpy
from bpy.props import StringProperty, BoolProperty, FloatVectorProperty, IntProperty
from bpy.types import NodeTree, NodeSocket, NodeSocketStandard

from sverchok import data_structure
from sverchok.data_structure import (
    updateNode,
    get_other_socket,
    socket_id,
    replace_socket)

from sverchok.core.socket_data import (
    SvGetSocketInfo,
    SvGetSocket,
    SvSetSocket,
    SvNoDataError,
    sentinel)

from sverchok.core.update_system import (
    build_update_list,
    process_from_node,
    process_tree,
    get_update_lists, update_error_nodes)

from sverchok.core.socket_conversions import (
    get_matrices_from_locs,
    get_locs_from_matrices,
    is_vector_to_matrix,
    is_matrix_to_vector)

from sverchok.ui import color_def


def process_from_socket(self, context):
    """Update function of exposed properties in Sockets"""
    self.node.process_node(context)


# this property group is only used by the old viewer draw
class SvColors(bpy.types.PropertyGroup):
    """ Class for colors CollectionProperty """
    color = FloatVectorProperty(
        name="svcolor", description="sverchok color",
        default=(0.055, 0.312, 0.5), min=0, max=1,
        step=1, precision=3, subtype='COLOR_GAMMA', size=3,
        update=updateNode)


class SvSocketCommon:
    @property
    def other(self):
        return get_other_socket(self)

    def set_default(self, value):
        if self.prop_name:
            setattr(self.node, self.prop_name, value)

    @property
    def socket_id(self):
        """Id of socket used by data_cache"""
        return str(hash(self.id_data.name + self.node.name + self.identifier))

    @property
    def index(self):
        """Index of socket"""
        node = self.node
        sockets = node.outputs if self.is_output else node.inputs
        for i, s in enumerate(sockets):
            if s == self:
                return i

    def sv_set(self, data):
        """Set output data"""
        SvSetSocket(self, data)

    def replace_socket(self, new_type, new_name=None):
        """Replace a socket with a socket of new_type and keep links,
        return the new socket, the old reference might be invalid"""
        return replace_socket(self, new_type, new_name)


class MatrixSocket(NodeSocket, SvSocketCommon):
    '''4x4 matrix Socket type'''
    bl_idname = "MatrixSocket"
    bl_label = "Matrix Socket"
    prop_name = StringProperty(default='')
    num_matrices = IntProperty(default=0)

    def get_prop_data(self):
        return {}

    def sv_get(self, default=sentinel, deepcopy=True):
        self.num_matrices = 0
        if self.is_linked and not self.is_output:

            if is_vector_to_matrix(self):
                # this means we're going to get a flat list of the incoming
                # locations and convert those into matrices proper.
                out = get_matrices_from_locs(SvGetSocket(self, deepcopy=True))
                self.num_matrices = len(out)
                return out

            return SvGetSocket(self, deepcopy)
        elif default is sentinel:
            raise SvNoDataError
        else:
            return default

    def draw(self, context, layout, node, text):
        if self.is_linked:
            draw_string = text + '. ' + SvGetSocketInfo(self)
            if is_vector_to_matrix(self):
                draw_string += (" (" + str(self.num_matrices) + ")")
            layout.label(draw_string)
        else:
            layout.label(text)

    def draw_color(self, context, node):
        '''if self.is_linked:
            return(.8,.3,.75,1.0)
        else: '''
        return (.2, .8, .8, 1.0)


class VerticesSocket(NodeSocket, SvSocketCommon):
    '''For vertex data'''
    bl_idname = "VerticesSocket"
    bl_label = "Vertices Socket"

    prop = FloatVectorProperty(default=(0, 0, 0), size=3, update=process_from_socket)
    prop_name = StringProperty(default='')
    use_prop = BoolProperty(default=False)

    def get_prop_data(self):
        if self.prop_name:
            return {"prop_name": socket.prop_name}
        elif self.use_prop:
            return {"use_prop": True,
                    "prop": self.prop[:]}
        else:
            return {}

    def sv_get(self, default=sentinel, deepcopy=True):
        if self.is_linked and not self.is_output:
            if is_matrix_to_vector(self):
                out = get_locs_from_matrices(SvGetSocket(self, deepcopy=True))
                return out

            return SvGetSocket(self, deepcopy)

        if self.prop_name:
            return [[getattr(self.node, self.prop_name)[:]]]
        elif self.use_prop:
            return [[self.prop[:]]]
        elif default is sentinel:
            raise SvNoDataError
        else:
            return default

    def draw(self, context, layout, node, text):
        if not self.is_output and not self.is_linked:
            if self.prop_name:
                layout.template_component_menu(node, self.prop_name, name=self.name)
            elif self.use_prop:
                layout.template_component_menu(self, "prop", name=self.name)
            else:
                layout.label(text)
        elif self.is_linked:
            layout.label(text + '. ' + SvGetSocketInfo(self))
        else:
            layout.label(text)

    def draw_color(self, context, node):
        return (0.9, 0.6, 0.2, 1.0)


class SvDummySocket(NodeSocket, SvSocketCommon):
    '''Dummy Socket for sockets awaiting assignment of type'''
    bl_idname = "SvDummySocket"
    bl_label = "Dummys Socket"

    prop = FloatVectorProperty(default=(0, 0, 0), size=3, update=process_from_socket)
    prop_name = StringProperty(default='')
    use_prop = BoolProperty(default=False)

    def get_prop_data(self):
        return self.other.get_prop_data()

    def sv_get(self):
        if self.is_linked:
            return self.links[0].bl_idname

    def sv_type_conversion(self, new_self):
        self = new_self

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.8, 0.8, 0.8, 0.3)


class StringsSocket(NodeSocket, SvSocketCommon):
    '''Generic, mostly numbers, socket type'''
    bl_idname = "StringsSocket"
    bl_label = "Strings Socket"

    prop_name = StringProperty(default='')

    prop_type = StringProperty(default='')
    prop_index = IntProperty()

    def get_prop_data(self):
        if self.prop_name:
            return {"prop_name": self.prop_name}
        elif self.prop_type:
            return {"prop_type": self.prop_type,
                    "prop_index": self.prop_index}
        else:
            return {}

    def sv_get(self, default=sentinel, deepcopy=True):
        if self.is_linked and not self.is_output:
            return SvGetSocket(self, deepcopy)
        elif self.prop_name:
            # to deal with subtype ANGLE, this solution should be considered temporary...
            _, prop_dict = getattr(self.node.rna_type, self.prop_name, (None, {}))
            subtype = prop_dict.get("subtype", "")
            if subtype == "ANGLE":
                return [[math.degrees(getattr(self.node, self.prop_name))]]
            return [[getattr(self.node, self.prop_name)]]
        elif self.prop_type:
            return [[getattr(self.node, self.prop_type)[self.prop_index]]]
        elif default is not sentinel:
            return default
        else:
            raise SvNoDataError

    def draw(self, context, layout, node, text):
        if self.prop_name:
            prop = node.rna_type.properties.get(self.prop_name, None)
            t = prop.name if prop else text
        else:
            t = text

        if not self.is_output and not self.is_linked:
            if self.prop_name and not self.prop_type:
                layout.prop(node, self.prop_name)
            elif self.prop_type:
                layout.prop(node, self.prop_type, index=self.prop_index, text=self.name)
            else:
                layout.label(t)
        elif self.is_linked:
            layout.label(t + '. ' + SvGetSocketInfo(self))
        else:
            layout.label(t)

    def draw_color(self, context, node):
        return (0.6, 1.0, 0.6, 1.0)


class SvNodeTreeCommon(object):
    '''
    Common methods shared between Sverchok node trees
    '''

    has_changed = BoolProperty(default=False)

    def build_update_list(self):
        build_update_list(self)

    def adjust_reroutes(self):

        reroutes = [n for n in self.nodes if n.bl_idname == 'NodeReroute']
        if not reroutes:
            return
        for n in reroutes:
            s = n.inputs[0]
            if s.links:
                self.freeze(True)

                other = get_other_socket(s)
                s_type = other.bl_idname
                if n.outputs[0].bl_idname != s_type:
                    out_socket = n.outputs.new(s_type, "Output")
                    in_sockets = [l.to_socket for l in n.outputs[0].links]
                    n.outputs.remove(n.outputs[0])
                    for i_s in in_sockets:
                        l = self.links.new(i_s, out_socket)

                self.unfreeze(True)

    def freeze(self, hard=False):
        if hard:
            self["don't update"] = 1
        elif not self.is_frozen():
            self["don't update"] = 0

    def is_frozen(self):
        return "don't update" in self

    def unfreeze(self, hard=False):
        if self.is_frozen():
            if hard or self["don't update"] == 0:
                del self["don't update"]

    def get_update_lists(self):
        return get_update_lists(self)

    @property
    def sv_trees(self):
        res = []
        for ng in bpy.data.node_groups:
            if ng.bl_idname in {'SverchCustomTreeType', 'SverchGroupTreeType'}:
                res.append(ng)
        return res


class SverchCustomTree(NodeTree, SvNodeTreeCommon):
    ''' Sverchok - architectural node programming of geometry in low level '''
    bl_idname = 'SverchCustomTreeType'
    bl_label = 'Sverchok Node Tree'
    bl_icon = 'RNA'

    def turn_off_ng(self, context):
        process_tree(self)

        # should turn off tree. for now it does by updating it whole
        # should work something like this
        # outputs = filter(lambda n: isinstance(n,SvOutput), self.nodes)
        # for node in outputs:
        #   node.disable()

    sv_animate = BoolProperty(name="Animate", default=True, description='Animate this layout')
    sv_show = BoolProperty(name="Show", default=True, description='Show this layout',
                           update=turn_off_ng)
    sv_bake = BoolProperty(name="Bake", default=True, description='Bake this layout')
    sv_process = BoolProperty(name="Process", default=True, description='Process layout')
    sv_user_colors = StringProperty(default="")

    # get update list for debug info, tuple (fulllist,dictofpartiallists)

    def update(self):
        '''
        Tags tree for update for handle
        '''
        self.has_changed = True

    def process_ani(self):
        """
        Process the Sverchok node tree if animation layers show true.
        For animation callback/handler
        """
        if self.sv_animate:
            process_tree(self)

    def process(self):
        """
        process the Sverchok tree upon editor changes from handler
        """
        if self.has_changed:
            self.build_update_list()
            self.has_changed = False
        if self.is_frozen():
            return
        if self.sv_process:
            process_tree(self)

        self.has_changed = False


class SverchCustomTreeNode:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname in ['SverchCustomTreeType', 'SverchGroupTreeType']

    @property
    def node_id(self):
        if not self.n_id:
            self.n_id = str(hash(self) ^ hash(time.monotonic()))
        return self.n_id

    def mark_error(self, err):
        """
        marks the with system error color
        will automaticly be cleared and restored to
        the old color
        """
        ng = self.id_data
        update_error_nodes(ng, self.name, err)

    def set_color(self):
        color = color_def.get_color(self.bl_idname)
        if color:
            self.use_custom_color = True
            self.color = color

    def create_sockets(self):
        '''Create node input and output sockets from
        their descriptions in self.input_descriptors and self.output_descriptors.
        '''

        if hasattr(self, "input_descriptors"):
            for descriptor in self.input_descriptors:
                descriptor.create(self)
        if hasattr(self, "output_descriptors"):
            for descriptor in self.output_descriptors:
                descriptor.create(self)

    def sv_init(self, context):
        self.create_sockets()

    def init(self, context):
        ng = self.id_data
        ng.freeze()
        if hasattr(self, "sv_init"):
            self.sv_init(context)
        self.set_color()
        ng.unfreeze()

    def process_node(self, context):
        '''
        Doesn't work as intended, inherited functions can't be used for bpy.props
        update= ...
        Still this is called from updateNode
        '''
        if self.id_data.bl_idname == "SverchCustomTreeType":
            if self.id_data.is_frozen():
                return

            if data_structure.DEBUG_MODE:
                a = time.perf_counter()
                process_from_node(self)
                b = time.perf_counter()
                print("Partial update from node", self.name, "in", round(b - a, 4))
            else:
                process_from_node(self)
        elif self.id_data.bl_idname == "SverchGroupTreeType":
            monad = self.id_data
            for instance in monad.instances:
                instance.process_node(context)
        else:
            pass


def register():
    bpy.utils.register_class(SvColors)
    bpy.utils.register_class(SverchCustomTree)
    bpy.utils.register_class(MatrixSocket)
    bpy.utils.register_class(StringsSocket)
    bpy.utils.register_class(VerticesSocket)
    bpy.utils.register_class(SvDummySocket)


def unregister():
    bpy.utils.unregister_class(SvDummySocket)
    bpy.utils.unregister_class(VerticesSocket)
    bpy.utils.unregister_class(StringsSocket)
    bpy.utils.unregister_class(MatrixSocket)
    bpy.utils.unregister_class(SverchCustomTree)
    bpy.utils.unregister_class(SvColors)
