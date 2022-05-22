# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from sverchok.dependencies import numba

local_numba_storage = {}

# further reading
# https://stackoverflow.com/a/54024922/1243487

def use_numba_if_possible(**kwargs):
    def wrapper(function_to_compile):
        if numba:
            from numba.pycc import CC
            cc = CC("numba_gofaster")
            # print(f"numba says: {kwargs=}")
            function_name = function_to_compile.__name__

            if function_name not in local_numba_storage:
                jitted_func = numba.njit(function_to_compile)
                local_numba_storage[function_name] = jitted_func
                #
                # --- compilse/write to disk here
                #
                cc.export(kwargs['name'], kwargs['sig'])(jitted_func)
                cc.compile()
            # elif function_name in disk_numba_storoage
            #
            # --- read from disk, store in local_numba_storage
            # 
            return local_numba_storage[function_name]
        else:
            return function_to_compile
    return wrapper
