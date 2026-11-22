# SPDX-License-Identifier: GPL-3.0-or-later
"""Optional accelerators, independent of Blender's dependency registry."""

try:
    import numba
except ImportError:
    numba = None


def njit(**options):
    def decorate(function):
        if numba is None:
            return function
        settings = dict(options)
        # One source tree is importable both as sv_mesh_core and through
        # Sverchok's package. Numba's disk cache embeds the import name.
        # Keep disk caching for the standalone name only to avoid loading a
        # cache which references an unavailable package in the other client.
        settings['cache'] = settings.get('cache', False) and function.__module__.startswith('sv_mesh_core.')
        return numba.njit(**settings)(function)
    return decorate


def scipy_tree():
    # Lazy: NumPy/Numba users need not pay SciPy's import cost.
    try:
        from scipy.spatial import cKDTree
    except ImportError as error:
        raise ImportError('The SCIPY backend requires scipy') from error
    return cKDTree


def has_scipy():
    # Avoid importing the large scipy package merely to select AUTO.
    from importlib.util import find_spec
    try:
        return find_spec('scipy') is not None
    except (ImportError, ValueError):
        return False
