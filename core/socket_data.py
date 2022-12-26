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

"""For internal usage of the sockets module"""

from collections import UserDict
from itertools import chain
from traceback import format_list, extract_stack
from typing import NewType, Optional, Literal

from bpy.types import NodeSocket
from sverchok.core.sv_custom_exceptions import SvNoDataError
from sverchok.utils.logging import debug
from sverchok.utils.handle_blender_data import BlTrees


SockId = NewType('SockId', str)


class DebugMemory(UserDict):
    _last_printed = dict()

    def __init__(self, data, print_all=True, print_trace=False):
        self.data = data
        self._print_all = print_all
        self._print_trace = print_trace

        self._id_sock: dict[SockId, NodeSocket] = dict()

        self._tree_len = 0
        self._node_len = 0
        self._sock_len = 0

        self._data_len = 100

    def __setitem__(self, key, value):
        if self._print_trace:
            for line in format_list(extract_stack()[4:-3]):
                print(line, end='')
        if key not in self.data:
            self.data[key] = value
            (self._pprint if self._print_all else self._pprint_id)(key, 'NEW')
        else:
            self.data[key] = value
            (self._pprint if self._print_all else self._pprint_id)(key, 'VALUE')

    def __delitem__(self, key):
        if self._print_trace:
            for line in format_list(extract_stack()[4:-3]):
                print(line, end='')
        (self._pprint if self._print_all else self._pprint_id)(key, 'DELETE')
        del self.data[key]

    def _pprint(self, changed_id, type_: Literal['NEW', 'DELETE', 'VALUE']):
        self._update_sockets()
        self._update_limits()

        print("SOCKETS DATA CACHE:")
        for id_, data in self.data.items():
            data = self._cut_text(str(data), self._data_len)
            if id_ == changed_id:
                if type_ == 'VALUE':
                    data = self._colorize(str(data), "GREEN")
                text = f"\t{self._to_address(id_, type_ != 'DELETE')}: {data},"
                if type_ == 'NEW':
                    print(self._colorize(text, "GREEN"))
                elif type_ == 'DELETE':
                    print(self._colorize(text, "RED"))
                else:
                    print(text)
            else:
                text = f"\t{self._to_address(id_)}: {data},"
                print(text)

    def _pprint_id(self, id_, type_: Literal['NEW', 'DELETE', 'VALUE']):
        self._update_sockets()
        self._update_limits()

        data = self.data[id_]
        data = self._cut_text(str(data), self._data_len)
        if type_ == 'VALUE':
            data = self._colorize(str(data), "GREEN")
        text = f"\t{self._to_address(id_, type_ != 'DELETE')}: {data},"
        if type_ == 'NEW':
            print(self._colorize(text, 'GREEN'))
        elif type_ == 'DELETE':
            print(self._colorize(text, 'RED'))
        else:
            print(text)

    def _update_sockets(self):
        self._id_sock.clear()
        for tree in BlTrees().sv_trees:
            for node in tree.nodes:
                for sock in chain(node.inputs, node.outputs):
                    if sock.bl_idname in {'NodeSocketVirtual', 'NodeSocketColor'}:
                        continue
                    if sock.socket_id in self._id_sock:
                        ds = self._id_sock[sock.socket_id]
                        debug(f"SOCKET ID DUPLICATION: "
                              f"1 - {ds.id_data.name} {ds.node.name=} {ds.name=}"
                              f"2 - {sock.id_data.name} {node.name=} {sock.name=}")
                    self._id_sock[sock.socket_id] = sock

    def _to_address(self, id_: SockId, colorize=True) -> str:
        if sock := self._id_sock.get(id_):
            return f"{sock.id_data.name:<{self._tree_len}}" \
                   f"|{sock.node.name:<{self._node_len}}" \
                   f"|{'out' if sock.is_output else 'in':<3}" \
                   f"|{sock.name:<{self._sock_len}}"
        else:
            return self._colorize(f"NOT FOUND ID({id_})", "YELLOW" if colorize else None)

    def _update_limits(self):
        for sock in self._id_sock.values():
            self._tree_len = max(self._tree_len, len(sock.id_data.name))
            self._node_len = max(self._node_len, len(sock.node.name))
            self._sock_len = max(self._sock_len, len(sock.name))

    @staticmethod
    def _colorize(text, color: Optional[Literal['GREEN', 'RED', 'YELLOW']] = None):
        if not color:
            return text
        elif color == 'GREEN':
            return f"\033[32m{text}\033[0m"
        elif color == 'RED':
            return f"\033[31m{text}\033[0m"
        elif color == 'YELLOW':
            return f"\033[33m{text}\033[0m"

    @staticmethod
    def _cut_text(text, max_size):
        if len(text) < max_size:
            return text
        else:
            start = text[:max_size//2-2]
            end = text[len(text) - (max_size//2-1):]
            return f"{start}...{end}"


socket_data_cache: dict[SockId, list] = dict()
# socket_data_cache = DebugMemory(socket_data_cache)


def sv_deep_copy(lst):
    """return deep copied data of list/tuple structure"""
    # faster than builtin deep copy for us.
    # useful for our limited case
    # we should be able to specify vectors here to get them create
    # or stop destroying them when in vector socket.
    if isinstance(lst, (list, tuple)):
        if lst and not isinstance(lst[0], (list, tuple)):
            return lst[:]
        return [sv_deep_copy(l) for l in lst]
    return lst


def sv_forget_socket(socket):
    """deletes socket data from cache"""
    try:
        del socket_data_cache[socket.socket_id]
    except KeyError:
        pass


def sv_set_socket(socket, data):
    """sets socket data for socket"""
    socket_data_cache[socket.socket_id] = data


def sv_get_socket(socket, deepcopy=True):
    """gets socket data from socket,
    if deep copy is True a deep copy is make_dep_dict,
    to increase performance if the node doesn't mutate input
    set to False and increase performance substanstilly
    """
    data = socket_data_cache.get(socket.socket_id)
    if data is not None:
        return sv_deep_copy(data) if deepcopy else data
    else:
        raise SvNoDataError(socket)


def get_output_socket_data(node, output_socket_name):
    """
    This method is intended to usage in internal tests mainly.
    Get data that the node has written to the output socket.
    Raises SvNoDataError if it hasn't written any.
    """
    socket = node.outputs[output_socket_name]
    sock_address = socket.socket_id
    if sock_address in socket_data_cache:
        return socket_data_cache[sock_address]
    else:
        raise SvNoDataError(socket)


def clear_all_socket_cache():
    """
    Reset socket cache for all node-trees.
    """
    socket_data_cache.clear()


def unregister():
    clear_all_socket_cache()
