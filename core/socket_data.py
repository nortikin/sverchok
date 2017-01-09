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

from sverchok import data_structure

#####################################
# socket data cache                 #
#####################################

sentinel = object()

# socket cache
socket_data_cache = {}

# faster than builtin deep copy for us.
# useful for our limited case
# we should be able to specify vectors here to get them create
# or stop destroying them when in vector socket.


def sv_deep_copy(lst):
    """return deep copied data of list/tuple structure"""
    if isinstance(lst, (list, tuple)):
        if lst and not isinstance(lst[0], (list, tuple)):
            return lst[:]
        return [sv_deep_copy(l) for l in lst]
    return lst


# Build string for showing in socket label
def SvGetSocketInfo(socket):
    """returns string to show in socket label"""
    global socket_data_cache
    ng = socket.id_data.name

    if socket.is_output:
        s_id = socket.socket_id
    elif socket.is_linked:
        s_id = socket.other.socket_id
    else:
        return ''
    if ng in socket_data_cache:
        if s_id in socket_data_cache[ng]:
            data = socket_data_cache[ng][s_id]
            if data:
                return str(len(data))
    return ''


def SvSetSocket(socket, out):
    """sets socket data for socket"""
    global socket_data_cache
    if data_structure.DEBUG_MODE:
        if not socket.is_output:
            print("Warning, {} setting input socket: {}".format(socket.node.name, socket.name))
        if not socket.is_linked:
            print("Warning: {} setting unconncted socket: {}".format(socket.node.name, socket.name))
    s_id = socket.socket_id
    s_ng = socket.id_data.name
    if s_ng not in socket_data_cache:
        socket_data_cache[s_ng] = {}
    socket_data_cache[s_ng][s_id] = out


def SvGetSocket(socket, deepcopy=True):
    """gets socket data from socket,
    if deep copy is True a deep copy is make_dep_dict,
    to increase performance if the node doesn't mutate input
    set to False and increase performance substanstilly
    """
    global socket_data_cache
    if socket.is_linked:
        other = socket.other
        s_id = other.socket_id
        s_ng = other.id_data.name
        if s_ng not in socket_data_cache:
            raise LookupError
        if s_id in socket_data_cache[s_ng]:
            out = socket_data_cache[s_ng][s_id]
            if deepcopy:
                return sv_deep_copy(out)
            else:
                return out
        else:
            if data_structure.DEBUG_MODE:
                print("cache miss:", socket.node.name, "->", socket.name, "from:", other.node.name, "->", other.name)
            raise SvNoDataError
    # not linked
    raise SvNoDataError

class SvNoDataError(LookupError):
    pass

def reset_socket_cache(ng):
    """
    Reset socket cache either for node group.
    """
    global socket_data_cache
    socket_data_cache[ng.name] = {}
