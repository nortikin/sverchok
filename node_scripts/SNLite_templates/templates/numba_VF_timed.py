"""
>in verts v    #
>in faces s    # no computation until both input sockets are connected
out _verts v
out _faces s
"""

from sverchok.utils.decorators_compilation import njit, numba_uncache
from sverchok.utils.context_managers import timed # timepart
# if other numba features are needed
# from sverchok.dependencies import numba

# there are two ways to clear sverchok's njit cache
#   1. numba_uncache(your_function_name)
#   2. rename the function, into something that does not yet exist in the cache

# this will compile, the first time it's run, then subsequent
# calls to your_function are from the cached compilation.

#@njit(cache=True)
def your_function(vlist, flist):
    return nvlist, nflist


for vlist, flist in zip(verts, faces):
    with timed(your_function) as your_function:
        v, f = your_function(vlist, flist)
    _verts.append(v)
    _faces.append(f)

# note,  sverchok.utils.context_managers.timepart allows you to time the duration of a context
#
# with timepart():
#    your code ..
