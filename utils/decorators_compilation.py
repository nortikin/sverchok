# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from sverchok.dependencies import numba


local_numba_storage = {}

# # further reading
# # https://stackoverflow.com/a/54024922/1243487

def eejit(**kwargs):
    def wrapper(function_to_compile):
        if numba:
            function_name = function_to_compile.__name__
            if function_name not in local_numba_storage:
                jitted_func = numba.njit(**kwargs)(function_to_compile)
                local_numba_storage[function_name] = jitted_func

            return local_numba_storage[function_name]
        else:
            return function_to_compile
    return wrapper

def njit(**kwargs):
    def wrapper(function_to_compile):
        return function_to_compile
    return wrapper