"""Portable mesh kernels. Import this package directly without loading Sverchok.

Add Sverchok's ``utils/mesh`` directory to PYTHONPATH, then import
``sv_mesh_core``. This package must never import bpy, bmesh or mathutils.
"""

from .buffers import RaggedArray

__all__ = ['RaggedArray']
