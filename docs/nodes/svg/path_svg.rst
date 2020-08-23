Path SVG
========

Functionality
-------------

Creates SVG paths.

Modes
-----

- Linear: Creates a polyline along the input vertices
- User: Creates a complex path using Letter commands to define segments


Inputs
------

- Vertices: Base vertices.
- Commands: Letters to define how to interpret the vertices data. Only in user mode.
- Fill / Stroke: Fill and Stroke attributes.


Commands
--------

One letter per segment, the last command will be repeated to match the verts length

      L = line segment (consumes 1 vertex)
      C = Bezier Curve (consumes 3 vertex)
      S = Smooth Bezier (consumes 2 vertex)
      Q = Quadratic curve (consumes 2 vertex)
      T = Smooth Quadratic (consumes 1 vertex)

If at the beginning of the command there are not enough vertices to feed the command it will be downgraded from C to S and from Q to T

If command Letter is not in the list [L, C, S, Q, T] it will be interpreted as L

Options
-------

- Cyclic: Join the end and the beginning of the path with a line segment

Outputs
-------

- SVG Objects


Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/svg/path_svg/blender_sverchok_path_svg_example_0.png

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/svg/path_svg/blender_sverchok_path_svg_example_1.png

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/svg/path_svg/blender_sverchok_path_svg_example_2.png
