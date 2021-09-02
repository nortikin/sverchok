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

from collections import defaultdict
from typing import Dict, NewType, Union, Optional

SockAddress = NewType('SockAddress', str)
SockContext = NewType('SockContext', str)  # socket can have multiple values in case it used inside node group
DataAddress = Dict[SockAddress, Dict[Union[SockContext, None], Optional[list]]]
socket_data_cache: DataAddress = defaultdict(lambda: defaultdict(lambda: None))


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
        del socket_data_cache[_get_sock_address(socket)]
    except KeyError:
        pass


def sv_set_socket(socket, data, context: SockContext = None):
    """sets socket data for socket"""
    socket_data_cache[_get_sock_address(socket)][context] = data


def sv_get_socket(socket, deepcopy=True, context: SockContext = None):
    """gets socket data from socket,
    if deep copy is True a deep copy is make_dep_dict,
    to increase performance if the node doesn't mutate input
    set to False and increase performance substanstilly
    """
    data = socket_data_cache[_get_sock_address(socket)][context]
    if data is not None:
        return sv_deep_copy(data) if deepcopy else data
    else:
        raise SvNoDataError(socket)


def _get_sock_address(sock) -> SockAddress:
    return sock.id_data.tree_id + sock.socket_id


class SvNoDataError(LookupError):
    def __init__(self, socket=None, node=None, msg=None):

        self.extra_message = msg if msg else ""

        if node is None and socket is not None:
            node = socket.node
        self.node = node
        self.socket = socket

        super(LookupError, self).__init__(self.get_message())

    def get_message(self):
        if self.extra_message:
            return f"node {self.socket.node.name} (socket {self.socket.name}) {self.extra_message}"
        if not self.node and not self.socket:
            return "SvNoDataError"
        else:
            return f"No data passed into socket '{self.socket.name}'"

    def __repr__(self):
        return self.get_message()

    def __str__(self):
        return repr(self)

    def __unicode__(self):
        return repr(self)

    def __format__(self, spec):
        return repr(self)


def get_output_socket_data(node, output_socket_name, context: SockContext = None):
    """
    This method is intended to usage in internal tests mainly.
    Get data that the node has written to the output socket.
    Raises SvNoDataError if it hasn't written any.
    """
    socket = node.inputs[output_socket_name]  # todo why output?
    sock_address = _get_sock_address(socket)
    if sock_address in socket_data_cache and context in socket_data_cache[sock_address]:
        return socket_data_cache[sock_address][context]
    else:
        raise SvNoDataError(socket)


def clear_all_socket_cache():
    """
    Reset socket cache for all node-trees.
    """
    socket_data_cache.clear()
