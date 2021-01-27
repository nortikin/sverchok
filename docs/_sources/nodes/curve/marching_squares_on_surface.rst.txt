Marching Squares on Surface
===========================

Dependencies
------------

This node requires SkImage_ library to work.

.. _SkImage: https://scikit-image.org/

Functionality
-------------

This node uses Marching Squres_ algorithm to find iso-lines of a scalar field
on an arbitrary surface, i.e. lines for which the value of scalar field equals
to the given value at each point. The lines are generated as mesh - vertices
and edges. You can use one of interpoolation nodes to build Curve objects from
them.

.. _Squares: https://en.wikipedia.org/wiki/Marching_squares

Inputs
------

This node has the following inputs:

* **Field**. Scalar field to generate iso-lines for. This input is mandatory.
* **Surface**. The surface to draw iso-lines on. This input is mandatory.
* **Value**. The value of scalar field, for which to generate iso-lines. The
  default value is 1.0.
* **SamplesU**, **SamplesV**. Number of samples along U and V parameter of the
  surface, correspondingly. This defines the resolution of curves: the bigger
  isvalue, the more vertices will the node generate, and the more precise the
  curves will be. But higher resolutioln requires more computation time. The
  default value is 50 for both inputs.

Parameters
----------

This node has the following parameters:

* **Join by surface**. If checked, then mesh objects generated for each
  separate contour on one surface will be merged into one mesh object.
  Otherwise, separate mesh object will be generated for each contour. Checked
  by default.
* **Counnect boundary**. If checked, the node will connect pieces of the same
  curve, that was split because it was cut by the boundary of the surface.
  Otherwise, several separate pieces will be generated in such case. Note that
  this node can not currently detect if the surface is closed to glue parts of
  contours at different sides of the surface. Checked by default. 

Outputs
-------

This node has the following outputs:

* **Vertices**. Generated iso-curves vertices in 3D space.
* **Edges**. Edges connecting iso-curve vertices.
* **UVVertices**. Points in surface's U/V space, corresponding to generated
  iso-curve vertices.

Examples of usage
-----------------

Find iso-curves of attractor field on a cylindrical surface:

.. image:: https://user-images.githubusercontent.com/284644/87060536-1418c400-c224-11ea-9e68-77c7f29c81fc.png

Another example with multiple surfaces:

.. image:: https://user-images.githubusercontent.com/284644/87062516-91453880-c226-11ea-9df8-8903de6d2ae2.png

