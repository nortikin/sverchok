"""
in verts v
out vout v
"""

def some_long_calculation():
    print("performing long calculation")
    return [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)]

#   There are many ways to store the state of a node, or cache a one off calculation
#
#   you can pickle, for persistence beyond the current blender session:
#      https://docs.python.org/3/library/pickle.html
#
#   snlite also has a few internal caches, one specifically implemented for runtime caching, it is the user_dict

# call this is you want to reset this instance of the cache
if False:
    reset_user_dict()

cache = get_user_dict()

# give it a useful key
if not (data := cache.get("current_state")):
    data = some_long_calculation()
    cache["current_state"] = data 

vout.append(data)
