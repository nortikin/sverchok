# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from __future__ import annotations

from collections import Mapping, defaultdict
from contextlib import contextmanager
from functools import wraps
from typing import List, Iterable, TypeVar, TYPE_CHECKING, Dict, Any, Generic, Optional, Union, NewType

import bpy

import sverchok.utils.tree_walk as tw
from sverchok.core.socket_data import sv_get_socket, sv_set_socket
from sverchok.utils.handle_blender_data import BlNode

if TYPE_CHECKING:
    from sverchok.core.node_group import SvGroupTree
    from sverchok.node_tree import SverchCustomTreeNode
    SvNode = Union[SverchCustomTreeNode, bpy.types.Node]


def _context_dependent(func):
    """Decorator for context dependent methods and properties. Raise error if context is not determined
    Decorated methods should have context argument and the class should have exec_context property"""
    @wraps(func)
    def inner(self, *args, **kwargs):
        if self.exec_context is None:
            raise RuntimeError("Before execution this method/property execution context should be determined")
        return func(self, *args, **kwargs)
    return inner


class Node(tw.Node):
    def __init__(self, name: str, index: int, tree: Tree, bl_node):
        self.name = name

        self._inputs: List[Socket] = []
        self._outputs: List[Socket] = []
        self._index = index
        self._tree = tree
        self._is_input_linked = None  # has links lead to group input nodes

        # cash
        self.bl_tween = bl_node

    # @property
    # def bl_tween(self) -> SvNode:
    #     """Quite expansive function, 1ms = 800 calls, it's better to cash, is potentially dangerous"""
    #     return self._tree.bl_tween.nodes[self._index]

    @property
    def id(self):
        return self.bl_tween.node_id

    @property
    @_context_dependent
    def is_updated(self):
        return ContextAttributes.get(self.id, 'is_updated',  False, self.exec_context)

    @is_updated.setter
    @_context_dependent
    def is_updated(self, status):
        ContextAttributes.set(self.id, 'is_updated', status, self.exec_context)

    @is_updated.deleter
    def is_updated(self):
        ContextAttributes.del_attr_data(self.id, 'is_updated')

    @property
    @_context_dependent
    def is_input_changed(self):
        return ContextAttributes.get(self.id, 'is_input_changed', True, self.exec_context)

    @is_input_changed.setter
    @_context_dependent
    def is_input_changed(self, status):
        ContextAttributes.set(self.id, 'is_input_changed', status, self.exec_context)

    @is_input_changed.deleter
    def is_input_changed(self):
        ContextAttributes.del_attr_data(self.id, 'is_input_changed')

    @property
    @_context_dependent
    def is_output_changed(self):
        return ContextAttributes.get(self.id, 'is_output_changed', True, self.exec_context)

    @is_output_changed.setter
    @_context_dependent
    def is_output_changed(self, status):
        ContextAttributes.set(self.id, 'is_output_changed', status, self.exec_context)

    @property
    @_context_dependent
    def error(self) -> Exception:
        return ContextAttributes.get(self.id, 'error', None, self.exec_context)

    @error.setter
    @_context_dependent
    def error(self, err: Exception):
        ContextAttributes.set(self.id, 'error', err, self.exec_context)

    @property
    @_context_dependent
    def update_time(self) -> float:
        return ContextAttributes.get(self.id, 'update_time', None, self.exec_context)

    @update_time.setter
    @_context_dependent
    def update_time(self, upd_time: float):
        ContextAttributes.set(self.id, 'update_time', upd_time, self.exec_context)

    @property
    def index(self):
        """Index of node location in Blender collection from which it was copied"""
        return self._index

    @property
    def inputs(self) -> List[Socket]:
        return self._inputs

    @property
    def outputs(self) -> List[Socket]:
        return self._outputs

    @property
    def next_nodes(self) -> Iterable[Node]:
        """Returns all nodes which are linked wia the node output sockets"""
        return {other_s.node for s in self.outputs for other_s in s.linked_sockets}

    @property
    def last_nodes(self) -> Iterable[Node]:
        """Returns all nodes which are linked wia the node input sockets"""
        return {other_s.node for s in self.inputs for other_s in s.linked_sockets}

    @property
    def is_input_linked(self) -> bool:
        if self._is_input_linked is None:  # or should it raise an error instead? and force user to call method manually
            self._tree.fill_is_input_linked()
        return self._is_input_linked

    @property
    def exec_context(self):
        """Return tree path if node is input linked and is not a debug otherwise empty path is returned"""
        return self._tree.exec_context if self.is_input_linked else ''
        # return self._tree.exec_context if not BlNode(self.bl_tween).is_debug_node and self.is_input_linked else ''

    def get_bl_node(self, tree: SvGroupTree) -> bpy.types.Node:
        """
        Will return the node from given tree with the same name
        It is slower then `bl_tween` attribute but can return node from another given tree
        """
        return tree.nodes[self.name]

    def get_input_socket(self, identifier: str, default=None) -> Optional[Socket]:
        """Search input socket by its identifier"""
        for socket in self._inputs:
            if socket.identifier == identifier:
                return socket
        return default

    def get_output_socket(self, identifier: str, default=None) -> Optional[Socket]:
        """Search output socket by its identifier"""
        for socket in self._outputs:
            if socket.identifier == identifier:
                return socket
        return default

    @classmethod
    def from_bl_node(cls, bl_node: bpy.types.Node, index: int, tree: Tree) -> Node:
        """Generate node and its sockets from Blender node instance"""
        node = cls(bl_node.name, index, tree, bl_node)
        for in_socket in bl_node.inputs:
            node.inputs.append(Socket.from_bl_socket(node, in_socket))
        for out_socket in bl_node.outputs:
            node.outputs.append(Socket.from_bl_socket(node, out_socket))
        return node

    def __repr__(self):
        return f'Node:"{self.name}"'


NodeType = TypeVar('NodeType', bound=Node)


class Tree(tw.Tree[NodeType]):
    """
    Structure similar to blender node groups but is more efficient in searching neighbours
    Each time when nodes or links collections are changed the instance of the tree should be recreated
    so it is immutable (topologically) data structure
    """
    def __init__(self, bl_tree: SvGroupTree):

        # it means that the tree has correct topology (during a tree initialization it's always true)
        self.is_updated = True

        self._tree_id = bl_tree.tree_id
        self._nodes = NodesCollection(bl_tree, self)
        self._links = LinksCollection(bl_tree, self)
        self._exec_context = None  # should be given to use tree data dependent on context (socket data, stats)

        # if the tree is created in the same time with the class initialization (loading file)
        # the index of the tree in node_groups collection will be not found (-1)
        self._index = bpy.data.node_groups.find(bl_tree.name)

        # add links between wifi nodes
        self._handle_wifi_nodes()

    @property
    def id(self) -> str:
        return self._tree_id

    @property
    def bl_tween(self) -> SvGroupTree:
        return bpy.data.node_groups[self._index]  # todo should keep real tree object instead

    @property
    def nodes(self) -> NodesCollection:
        return self._nodes

    @property
    def links(self) -> LinksCollection:
        return self._links

    def fill_is_input_linked(self):  # it can get type of input nodes optionally later
        for node in self.nodes:
            node._is_input_linked = False
        for node in self.bfs_walk([self.nodes.active_input] if self.nodes.active_output else []):
            node._is_input_linked = True

    @contextmanager
    def set_exec_context(self, context: str = ''):  # todo should be context type imported?
        if self._exec_context is not None:
            raise RuntimeError("Tree already has execution context")
        self._exec_context = context
        try:
            yield None
        finally:
            self._exec_context = None

    @property
    def exec_context(self):
        return self._exec_context

    def delete(self):
        """Free context data"""
        for node in self.nodes:
            ContextAttributes.del_obj_data(node.id)

    def _handle_wifi_nodes(self):
        """The idea is to convert wifi nodes into regular nodes with sockets and links between them"""
        # todo the code is very bad and should be removed later wifi node refactoring
        # the method knows too match about wifi nodes
        var_name_wifi_in = dict()

        # add sockets to wifi "from nodes" if it has variable
        for node in self._nodes:
            if node.bl_tween.bl_idname == 'WifiInNode' and node.bl_tween.var_name:
                socket = Socket(node, True, "Virtual wifi socket")
                node.outputs.append(socket)
                var_name_wifi_in[node.bl_tween.var_name] = node

        # add sockets to wifi "to nodes" and connect them to wifi "from nodes" if there is wifi node with such variable
        if var_name_wifi_in:
            for to_node in self._nodes:
                if to_node.bl_tween.bl_idname == 'WifiOutNode' and to_node.bl_tween.var_name in var_name_wifi_in:
                    socket = Socket(to_node, False, "Virtual wifi socket")
                    to_node.inputs.append(socket)
                    from_node = var_name_wifi_in[to_node.bl_tween.var_name]
                    from_socket = from_node.outputs[0]
                    to_socket = to_node.inputs[0]
                    self.links._dict[
                        (from_node.name, from_socket.identifier,
                         to_node.name, to_socket.identifier)] = Link(from_socket, to_socket, len(self.links))


Element = TypeVar('Element')


class TreeCollections(Mapping, Generic[Element]):
    """
    The idea of this collection is to have access to its elements by their identifier
    and meantime to have access to their indexes of true blender collections
    so to get fast mapping between python and blender collections
    downside is that this collection is immutable
    because it impossible to predict order of Blender collection after changing of their content
    """
    def __init__(self):
        self._dict: Dict[Any, Element] = dict()

    def __getitem__(self, item) -> Element:
        return self._dict[item]

    def __iter__(self) -> Iterable[Element]:
        return iter(self._dict.values())

    def __len__(self):
        return len(self._dict)

    def __contains__(self, item):
        try:
            return item.name in self._dict
        except AttributeError:
            return item in self._dict

    def __sub__(self, other) -> List[Element]:
        if isinstance(other, TreeCollections):
            return [self._dict[k] for k in (self._dict.keys() - other._dict.keys())]
        else:
            return NotImplemented


class NodesCollection(TreeCollections[NodeType]):
    def __init__(self, bl_tree: SvGroupTree, tree: Tree):
        """Generate Python representation of Blender nodes. Reroute and frame nodes are ignored"""
        super().__init__()
        self._active_input: Optional[Node] = None
        self._active_output: Optional[Node] = None
        for i, bl_node in enumerate(bl_tree.nodes):
            if bl_node.bl_idname in {'NodeReroute', 'NodeFrame'}:
                continue
            node = Node.from_bl_node(bl_node, i, tree)
            self._dict[bl_node.name] = node

            # https://developer.blender.org/T82350
            if bl_node.bl_idname == 'NodeGroupInput':
                self._active_input = node
            if bl_node.bl_idname == 'NodeGroupOutput':
                self._active_output = node

    @property
    def active_input(self) -> Optional[Node]:
        return self._active_input

    @property
    def active_output(self) -> Optional[Node]:
        return self._active_output


class LinksCollection(TreeCollections):
    def __init__(self, bl_tree: SvGroupTree, tree: Tree):
        """Generate Python representation of Blender links. Reroute nodes are thrown from the tree model.
        Muted links are ignored"""
        super().__init__()

        # helping data structure for fast link search
        from_node_links = defaultdict(list)
        for bl_link in bl_tree.links:
            from_node_links[bl_link.from_node].append(bl_link)

        for i, bl_link in enumerate(bl_tree.links):

            # new in 2.93, it is the same as if there was no the link (is_hidden was added before 2.93)
            if hasattr(bl_link, 'is_muted') and bl_link.is_muted:
                # or bl_link.is_hidden:  # it does not call update method of a tree https://developer.blender.org/T89109
                continue

            # link from reroute node to be ignored
            from_bl_node = bl_link.from_node
            if from_bl_node.bl_idname == 'NodeReroute':
                continue

            # link to normal node should be found
            to_bl_node = bl_link.to_node
            if to_bl_node.bl_idname == 'NodeReroute':
                next_links = from_node_links[bl_link.to_node].copy()
                to_links = []
                while next_links:
                    next_link = next_links.pop()
                    if next_link.to_node.bl_idname == 'NodeReroute':
                        next_links.extend(from_node_links[next_link.to_node])
                    else:
                        to_links.append(next_link)
            else:
                to_links = [bl_link]

            # generate link(s)
            for to_link in to_links:
                from_node = tree.nodes[bl_link.from_node.name]
                from_socket = from_node.get_output_socket(bl_link.from_socket.identifier)
                to_node = tree.nodes[to_link.to_node.name]
                to_socket = to_node.get_input_socket(to_link.to_socket.identifier)

                self._dict[(from_node.name, from_socket.identifier,
                            to_node.name, to_socket.identifier)] = Link(from_socket, to_socket, i)

    def __iter__(self) -> Iterable[Link]: return super().__iter__()


class Socket:
    def __init__(self, node: Node, is_output: bool, identifier: str):
        self.is_output = is_output
        self.identifier = identifier
        self._node = node
        self._links = []

    @property
    def bl_tween(self) -> bpy.types.NodeSocket:
        return getattr(self._node.bl_tween, 'outputs' if self.is_output else 'inputs')[self.index]

    @property
    def index(self) -> int:
        """Index of the node in inputs or outputs collection"""
        return getattr(self.node, 'outputs' if self.is_output else 'inputs').index(self)

    @property
    def node(self) -> Node:
        return self._node

    @property
    def links(self) -> List[Link]:
        return self._links

    @property
    def exec_context(self):
        return self._node.exec_context

    @property
    @_context_dependent
    def data(self):
        return sv_get_socket(self.bl_tween, False, self.exec_context)

    @data.setter
    @_context_dependent
    def data(self, data):
        sv_set_socket(self.bl_tween, data, self.exec_context)

    def get_bl_socket(self, bl_tree: SvGroupTree) -> bpy.types.NodeSocket:
        """Search socket in given tree by its identifier"""
        bl_node = self.node.get_bl_node(bl_tree)
        for bl_socket in bl_node.outputs if self.is_output else bl_node.inputs:
            if bl_socket.identifier == self.identifier:
                return bl_socket
        raise LookupError(f'Socket "{self.identifier}" was not found in Node "{bl_node.name}"'
                          f'in {"outputs" if self.is_output else "inputs"} sockets:'
                          f'"{[s.identefier for s in (bl_node.outputs if self.is_output else bl_node.inputs)]}"')

    @property
    def linked_sockets(self) -> List[Socket]:
        """All sockets which share the same links"""
        return [link.to_socket if self.is_output else link.from_socket for link in self.links]

    @classmethod
    def from_bl_socket(cls, node: Node, bl_socket: bpy.types.NodeSocket) -> Socket:
        """Generate socket from Blender socket instance"""
        return cls(node, bl_socket.is_output, bl_socket.identifier)

    def __repr__(self):
        return f'Socket "{self.identifier}"'


class Link:
    def __init__(self, from_socket: Socket, to_socket: Socket, index: int):
        self.from_socket: Socket = from_socket
        self.to_socket: Socket = to_socket
        from_socket.links.append(self)
        to_socket.links.append(self)

        self._index = index

    @property
    def index(self):
        """Index of the link location in Blender collection from which it was copied"""
        return self._index

    @property
    def from_node(self) -> Node:
        return self.from_socket.node

    @property
    def to_node(self) -> Node:
        return self.to_socket.node

    def __repr__(self):
        return f'FROM "{self.from_node.name}.{self.from_socket.identifier}" ' \
               f'TO "{self.to_node.name}.{self.to_socket.identifier}"'


class ContextAttributes:
    """It keeps attributes which should be preserved between tree evaluations
    also it should keep those attributes which can have different values depending on context execution
    first scenario related with nature of Blender tree data structure which each time should be converted into
    Python data structure for efficient search
    second scenario is related with nature of node groups where a node can have different input dependent on
    a group node from which execution has began"""

    ObjectId = NewType('ObjectId', str)
    AttrName = NewType('AttrName', str)
    Context = NewType('Context', str)  # context id
    DataAddress = Dict[ObjectId, Dict[AttrName, Dict[Context, Any]]]
    _socket_data_cache: DataAddress = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: None)))

    @classmethod
    def set(cls, object_id: ObjectId, attr_name: AttrName, data, context: Context = ''):
        """Save data of attribute of an object. Context allow ot have multiple values per attribute"""
        cls._socket_data_cache[object_id][attr_name][context] = data

    @classmethod
    def get(cls, object_id: ObjectId, attr_name: AttrName, default=..., context: Context = ''):
        """Get saved data of attribute of given object. Context determines multiple values for the same attribute"""
        data = cls._socket_data_cache[object_id][attr_name][context]
        if data is None and default is ...:
            raise LookupError("Given object does not have any data")
        else:
            return default if data is None else data

    @classmethod
    def del_obj_data(cls, object_id: ObjectId):
        """Deletes all attributes of given object"""
        try:
            del cls._socket_data_cache[object_id]
        except KeyError:
            pass

    @classmethod
    def del_attr_data(cls, object_id: ObjectId, attr_name: AttrName):
        """Delete all data of attribute of given object"""
        try:
            del cls._socket_data_cache[object_id][attr_name]
        except KeyError:
            pass
