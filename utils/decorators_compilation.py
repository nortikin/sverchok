# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from sverchok.dependencies import numba



local_numba_storage = {}

def use_numba_if_possible(function_to_compile):
    if numba:
        function_name = function_to_compile.__name__
        if function_name not in local_numba_storage:
            local_numba_storage[function_name] = numba.njit(function_to_compile)
        return local_numba_storage[function_name]
    else:
        return function_to_compile
