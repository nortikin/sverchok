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

import inspect
from math import *

from mathutils import Vector, Matrix

from sverchok.utils.sv_script import SvScript
from sverchok.utils.math import sign

def load_script(source, file_name):
    from_file = '<{}>'.format(file_name)
    code = compile(source, from_file, 'exec', optimize=0)
    # insert classes that we can inherit from
    local_space = {cls.__name__:cls for cls in SvScript.__subclasses__()}
    base_classes = set(cls.__name__ for cls in SvScript.__subclasses__())
    local_space["SvScript"] = SvScript
    
    exec(code, globals(),local_space)

    script = None
    
    for name in code.co_names:
        # filter out inherited
        if not name in local_space:
            continue
        # skip base classes
        if name in base_classes:
            continue        
            
        try: 
            script_class = local_space.get(name)
            if inspect.isclass(script_class):
                script = script_class()
                if isinstance(script, SvScript):
                    print("Script Node found script {}".format(name))
                    script = script
                    globals().update(local_space)
                    
        except Exception as Err:
            print("Script Node couldn't load {0}".format(name))
            print(Err) 
            
    if not script:
        raise ImportWarning("Couldn't find script in {}".format(name))  
    return script
    
def make_functions_dict(*functions):
    return dict([(function.__name__, function) for function in functions])

# Functions
safe_names = make_functions_dict(
        # From math module
        acos, acosh, asin, asinh, atan, atan2,
        atanh, ceil, copysign, cos, cosh, degrees,
        erf, erfc, exp, expm1, fabs, factorial, floor,
        fmod, frexp, fsum, gamma, hypot, isfinite, isinf,
        isnan, ldexp, lgamma, log, log10, log1p, log2, modf,
        pow, radians, sin, sinh, sqrt, tan, tanh, trunc,
        # Additional functions
        abs, sign,
        # From mathutlis module
        Vector, Matrix,
        # Python type conversions
        tuple, list, str, dict
    )
# Constants
safe_names['e'] = e
safe_names['pi'] = pi

# Blender modules
# Consider this not safe for now
# safe_names["bpy"] = bpy

