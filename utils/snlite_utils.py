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


import bpy

from sverchok.data_structure import match_long_repeat


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



static_caching = {}
responsive_caching = {}


class CacheMixin():


    def wipe_static_cache(self):
        try:
            del static_caching[self.node_id]
        except Exception as err:
            msg_1 = f"{self.node_id} not found in static_caching.."
            msg_2 = f"size static cache = {len(static_caching)}"
            self.info(f"{msg_1}\n{msg_2}")
            self.info(f"{err}")



    def get_static_cache(self, function_to_use=None, variables=None):
        """
        This function provides a relatively convenient way to do Static Caching

        - lets you cache one off calculations for this node
        - reset the cache if your (input) data changes.

        How to make an initial cache for a tested function with known input data:

            # if you need to reset, do it above the caching.
            self.wipe_static_cache()

            # here you set the cache, and obtain the data.
            my_data = self.get_static_cache(
                my_useful_function,    # any kind of function, should return the useful product of calculation
                my_variables           # must be a tuple of variables (if single variable use (variable,))
                                       # if no variables use () : f.ex:  self.get_static_cache(some_func, ())
        
        """
      
        cache = static_caching.get(self.node_id)
        if not cache:
            cache = function_to_use(*variables)
            static_caching[self.node_id] = cache
            self.info('static cache created')

        return cache

    def wipe_responsive_cache(self, function_to_use=None):
        """
        can wipe the value stored in a key is found where the first two components are (self.node_id, function_str_hash, .......)

        """
        try:
            for k in responsive_caching.keys():
                if k[0] == self.node_id and k[1] == hash(inspect.getsource(function_to_use)):
                    del responsive_caching[k]
                    self.info(f"removed key: {self.nod_id}, function: {function_to_use.__name__}")
                    # break  maybe 

        except Exception as err:
            self.info(err)

    def get_responsive_cache(self, function_to_use=None, variables=None):
        """
        this functions aims to provide a way to check if a the function or variables that produce your data
        has changed, before deciding to re-execute the function with your variables.
        - if the function changes significantly (any non whitespace change)  (no point comparing object references)
        - or the variables (works best if the number of variables are relatively small, and not f.ex 100k points)

        [x] check the function code as a string
        [x] check the input variables


        """
        component_function_text = hash(inspect.getsource(function_to_use))
        component_variables_hash = hash(str(variables))
        cache_key = (self.node_id, component_function_text, component_variables_hash)

        cache = responsive_caching.get(cache_key)

        if not cache:
            cache = function_to_use(*variables_to_use)
            responsive_caching[cache_key] = cache
            self.info('responsive cache created')

            # if any other cache_key is similar except variables, then probably..probably.. want to nuke it.
            ...

        return cache
