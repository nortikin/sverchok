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

import functools
import inspect
import warnings

string_types = (type(b''), type(u''))


def deprecated(argument):
    """
    This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.
    """

    def format_message(object, reason):
        if inspect.isclass(object):
            if reason is None:
                fmt = "Call to deprecated class {name}."
                return fmt.format(name = object.__name__)
            else:
                fmt = "Call to deprecated class {name} ({reason})."
                return fmt.format(name = object.__name__, reason = reason)
        elif inspect.isfunction(object):
            if reason is None:
                fmt = "Call to deprecated function {name}."
                return fmt.format(name = object.__name__)
            else: 
                fmt = "Call to deprecated function {name} ({reason})."
                return fmt.format(name = object.__name__, reason = reason)
        else:
            raise TypeError("Unexpected deprecated object type: " + repr(type(object)))

    if isinstance(argument, string_types):

        # The @deprecated is used with a 'reason'.
        #
        # .. code-block:: python
        #
        #    @deprecated("please, use another function")
        #    def old_function(x, y):
        #      pass

        reason = argument

        def decorator(func):
            @functools.wraps(func)
            def wrapped(*args, **kwargs):
                warnings.simplefilter('always', DeprecationWarning)
                warnings.warn(
                    format_message(func, reason),
                    category=DeprecationWarning,
                    stacklevel=2
                )
                warnings.simplefilter('default', DeprecationWarning)
                return func(*args, **kwargs)
            return wrapped
        return decorator

    else:
        # The @deprecated is used without any 'reason'.
        #
        # .. code-block:: python
        #
        #    @deprecated
        #    def old_function(x, y):
        #      pass

        func = argument
        reason = None

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            warnings.simplefilter('always', DeprecationWarning)
            warnings.warn(
                format_message(func, reason),
                category=DeprecationWarning,
                stacklevel=2
            )
            warnings.simplefilter('default', DeprecationWarning)
            return func(*args, **kwargs)

        return wrapped

        



