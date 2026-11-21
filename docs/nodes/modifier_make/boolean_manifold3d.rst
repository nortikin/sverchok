Boolean Manifold3D
==================

.. image:: https://raw.githubusercontent.com/kevinsmia1939/images/refs/heads/main/sverchok%20screenshot/functionality.png
  :target: https://raw.githubusercontent.com/kevinsmia1939/images/refs/heads/main/sverchok%20screenshot/functionality.png

Functionality
-------------

This node uses an external library called Manifold3d to perform boolean operations (Intersect, Union, and Difference). Blender3d internally uses the same library, it's fast and reliable.

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

Notes
--------
Until bmesh-based boolean APIs are available, this is a tidy solution.
This is the pull request that adds this node: https://github.com/nortikin/sverchok/pull/5190

Alternatives
------------
CSG Boolean: https://nortikin.github.io/sverchok/docs/nodes/modifier_make/csg_booleanMK2.html
Blender Internal: 
FreeCAD based booleans: https://github.com/nortikin/sverchok/issues/3430
