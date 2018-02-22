# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from sverchok.utils.context_managers import sv_preferences

def get_val(param_name):
    with sv_preferences() as prefs:
        return getattr(prefs, param_name)



def set_vals(**kwargs):
    with sv_preferences() as prefs:
        for key, val in kwargs.items():
            print('set: key({0}) = value({1})'.format(key, val))
            try:
                setattr(prefs, key, val)
            except Exception as err:
                print(err)
                print('failed prefs.{0}={1}'.format(key, val))


# usage of get_val, set_vals
#
# from sverchok.utils.sv_prefs import get_val, set_vals
#
# ...
# 
#     m = get_val("some_property")
#
#     set_vals(some_property=somevalue, some_property2=somevalue2)
#
