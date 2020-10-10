# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import zip_longest

class SvDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """
        Special attribute for keeping meta data which helps to unwrap dictionaries properly for `dictionary out` node
        This attribute should be set only by nodes which create new dictionaries or change existing one
        Order of keys in `self.inputs` dictionary should be the same as order of input data of the dictionary
        `self.inputs` dictionary should keep data in next format:
        {data.id:  # it helps to track data, if is changed `dictionary out` recreate new socket for this data
            {'type': any socket type with which input data is related,
             'name': name of output socket,
             'nest': only for 'SvDictionarySocket' type, should keep dictionary with the same data structure
             }}
             
        For example, there is the dictionary:
        dict('My values': [0,1,2], 'My vertices': [(0,0,0), (1,0,0), (0,1,0)])
        
        Metadata should look in this way:
        self.inputs = {'Values id':
                           {'type': 'SvStringsSocket',
                           {'name': 'My values',
                           {'nest': None
                           }
                      'Vertices id':
                          {'type': 'SvVerticesSocket',
                          {'name': 'My vertices',
                          {'nest': None
                          }
                      }
        """
        self.inputs = dict()

    @staticmethod
    def get_inputs(d):
        if isinstance(d, SvDict) and d.inputs:
            return d.inputs
        else:
            inputs = {}
            for key in d:
                inputs[key] = {
                        'type': 'SvStringsSocket',
                        'name': key,
                        'nest': None
                    }
            return inputs

    def get_max_nesting_level(self):
        max_level = 0
        for key, value in self.items():
            if isinstance(value, SvDict):
                level = value.get_max_nesting_level() + 1
            elif isinstance(value, dict):
                level = SvDict(value).get_max_nesting_level() + 1
            else:
                level = 0
            if level > max_level:
                max_level = level
        return max_level

    def get_nested_keys_at(self, level):
        if level == 0:
            return set(self.keys())
        else:
            keys = set()
            for value in self.values():
                if isinstance(value, SvDict):
                    v_keys = value.get_nested_keys_at(level-1)
                elif isinstance(value, dict):
                    v_keys = SvDict(value).get_nested_keys_at(level-1)
                else:
                    v_keys = set()
                keys.update(v_keys)
            return keys

    def get_nested_inputs_at(self, level):
        if level == 0:
            return SvDict.get_inputs(self)
        else:
            inputs = dict()
            for value in self.values():
                if isinstance(value, SvDict):
                    v_inputs = value.get_nested_inputs_at(level-1)
                elif isinstance(value, dict):
                    v_inputs = SvDict(value).get_nested_inputs_at(level-1)
                else:
                    v_inputs = None
                if v_inputs:
                    inputs.update(v_inputs)
            return inputs

    def get_all_nested_keys(self):
        max_level = self.get_max_nesting_level()
        all_keys = []
        for level in range(max_level):
            keys = self.get_nested_keys_at(level)
            all_keys.append(keys)
        return all_keys

    def get_sock_types(self, level=0):
        if level == 0:
            inputs = SvDict.get_inputs(self)
            return [input['type'] for input in inputs.values()]
        else:
            types = None
            for value in self.values():
                if isinstance(value, SvDict):
                    v_types = value.get_sock_types(level-1)
                elif isinstance(value, dict):
                    v_types = SvDict(value).get_sock_types(level-1)
                else:
                    v_types = None

                if v_types:
                    if types is None:
                        types = v_types
                    else:
                        for i, (old_type, new_type) in enumerate(zip_longest(types, v_types)):
                            if old_type is None:
                                types[i] = new_type
                            elif old_type != new_type:
                                types[i] = 'SvStringsSocket'
            return types

