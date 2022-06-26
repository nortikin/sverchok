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

def njit(**kwargs):
    if numba:

        def wrapper(function_to_compile):
            function_name = function_to_compile.__name__
            if function_name not in local_numba_storage:
                jitted_func = numba.njit(**kwargs)(function_to_compile)
                local_numba_storage[function_name] = jitted_func
            
            #elif function_name in local_numba_storage and function_str_hash doesn't match:
            #    # recache
            # the dowside to this would be that it becomes whitespace/comment changes sensitive
            # unless whitespace and comments are removed from functionstring before compilation..

            return local_numba_storage[function_name]

    else:

        def wrapper(function_to_compile):
            return function_to_compile

    return wrapper


def jit(**kwargs):
    if numba:

        def wrapper(function_to_compile):
            function_name = function_to_compile.__name__
            if function_name not in local_numba_storage:
                jitted_func = numba.jit(**kwargs)(function_to_compile)
                local_numba_storage[function_name] = jitted_func
            return local_numba_storage[function_name]

    else:

        def wrapper(function_to_compile):
            return function_to_compile

    return wrapper

def numba_uncache(function_name):
    del local_numba_storage[function_name]
