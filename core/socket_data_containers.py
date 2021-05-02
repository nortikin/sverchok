# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


"""
The purpose of this module is to keep classes fo socket data containers
Usually such containers are just lists but in trick cases it requires more customization
"""


from typing import List, Union, Iterable

import bpy
from sverchok.utils.handle_blender_data import BPYPointers


class SocketData:
    """It should posses such method as 'copy', 'wrap', 'unwrap' and etc. later"""

    def get_data(self):
        """This method will be called in socket.sv_get method"""
        raise NotImplementedError(f'"get_data" method is not implemented in "{type(self).__name__}" class')

    def __len__(self):
        """return number of objects for showing in socket names"""
        raise NotImplementedError(f'"len" method is not implemented in "{type(self).__name__}" class')


class ObjectSocketData(SocketData):
    """It will store meta information for refreshing links to given objects"""

    def __init__(self, data: list):
        """Data is list of objects or list of lists of objects. Object can be all types of bpy.data"""
        self._data = data

        # meta data of the same shape as input data
        self._collection_names: Union[List[str], List[list]] = self._apply_func_it(self._get_col_name, data)
        self._object_names: Union[List[str], List[list]] = self._apply_func_it(self._get_block_name, data)

    def get_data(self):
        """It will refresh references to data if necessary"""

        def refresh_data(col_name, name):
            # this potentially can be slow, solution could be create separate class for cashing searches
            return getattr(bpy.data, col_name).get(name)

        def first_none_iter(it):
            # should be moved somewhere
            return first_none_iter(next(iter(it))) if isinstance(it, Iterable) else it

        # assume that either all blocks are invalid or none
        if not self._is_valid_reference(first_none_iter(self._data)):
            print('Outdated Object data detected - fixing')  # todo remove
            self._data = self._apply_func_its(refresh_data, self._collection_names, self._object_names)

        return self._data

    @staticmethod
    def _get_col_name(block):
        return BPYPointers.get_type(block.bl_rna).collection_name

    @staticmethod
    def _get_block_name(block):
        return block.name

    @staticmethod
    def _is_valid_reference(obj) -> bool:
        """Test of keeping valid references to a data block, should be moved in another location later"""
        try:
            obj.name  # assume that all given data blocks has name property
            return True
        except ReferenceError:
            return False

    def _apply_func_it(self, func, it: Iterable) -> list:
        """Apply function to none iterable elements. Input shape is unchanged.
        Should be moved in another module later"""
        out = []
        for i in it:
            if isinstance(i, Iterable):
                out.append(self._apply_func_it(func, i))
            else:
                out.append(func(i))
        return out

    def _apply_func_its(self, func, *its: Iterable) -> list:
        """
        Apply function to none iterable elements. Input shape is unchanged.
        Can get multiple iterables with the same shape.
        func should have the same number of arguments as input iterables.

        Should be moved in another module later
        _apply_func_its(lambda a, b: a + b, [1,[2,3],4], [5,[6,7],8])
        -> [6, [8, 10], 12]
        """
        out = []
        for i in zip(*its):
            if isinstance(i[0], Iterable) and not isinstance(i[0], str):
                out.append(self._apply_func_its(func, *i))
            else:
                out.append(func(*i))
        return out

    def __len__(self):
        return len(self._data)
