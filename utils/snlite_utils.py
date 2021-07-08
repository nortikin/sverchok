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


from logging import info

import bpy
from sverchok.data_structure import match_long_repeat
from sverchok.dependencies import numba

njit_function_storage = {}


def vectorize(all_data):

    def listify(data):
        if isinstance(data, (int, float)):
            data = [data]
        return data

    for idx, d in enumerate(all_data):
        all_data[idx] = listify(d)

    return match_long_repeat(all_data)


def ddir(content, filter_str=None):
    vals = []
    if not filter_str:
        vals = [n for n in dir(content) if not n.startswith('__')]
    else:
        vals = [n for n in dir(content) if not n.startswith('__') and filter_str in n]
    return vals


def sv_njit(function_to_njit, parameters):
    fn_name = function_to_njit.__name__
    njit_func = njit_function_storage.get(fn_name)
    if not njit_func:

        if numba:
            numba.njit(function_to_njit)

        result = function_to_njit(*parameters)
        njit_function_storage[fn_name] = function_to_njit
        info(f"caching function: {fn_name}")
    else:
        result = njit_func(*parameters)
    return result

def sv_njit_clear(function_to_njit):
    fn_name = function_to_njit.__name__
    njit_func = njit_function_storage.get(fn_name)
    if njit_func:
        del njit_function_storage[fn_name]
        info(f"cleared cached function: {fn_name}")
