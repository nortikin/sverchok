Internal Boolean
================

.. image:: https://raw.githubusercontent.com/kevinsmia1939/images/refs/heads/main/sverchok%20screenshot/functionality.png
  :target: https://raw.githubusercontent.com/kevinsmia1939/images/refs/heads/main/sverchok%20screenshot/functionality.png

Functionality
-------------

This node implements Blender's internal boolean modifier with 3 functions: Intersect, Union, and Difference.
Solver options include Fast and Exact solvers. Fast Solver is simpler and faster but does not support overlapping geometries, which Exact Solver does support overlapping geometries but is slower than the Fast Solver.

More information on Blender's internal boolean modifier can be found here:
https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/booleans.html

.. image:: https://raw.githubusercontent.com/kevinsmia1939/images/refs/heads/main/sverchok%20screenshot/node.png
  :target: https://raw.githubusercontent.com/kevinsmia1939/images/refs/heads/main/sverchok%20screenshot/node.png

There are switches and modes.

- Nested Accumulate (bool first two objects, then applies the rest to the result one by one.
- Only final result (output only last iteration result)

.. image:: https://raw.githubusercontent.com/kevinsmia1939/images/refs/heads/main/sverchok%20screenshot/example.png
  :target: https://raw.githubusercontent.com/kevinsmia1939/images/refs/heads/main/sverchok%20screenshot/example.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

warnings
--------
This implementation creates a temporary object and converts data back, which adds overhead. Might become quickly sluggish with many objects. Until bmesh-based boolean APIs are available, this will be a workaround solution.
This is the pull request that adds this node: https://github.com/nortikin/sverchok/pull/5190

Alternatives
------------
CSG Boolean: https://nortikin.github.io/sverchok/docs/nodes/modifier_make/csg_booleanMK2.html
You might be interested in the FreeCAD implementation discussed here. https://github.com/nortikin/sverchok/issues/3430

