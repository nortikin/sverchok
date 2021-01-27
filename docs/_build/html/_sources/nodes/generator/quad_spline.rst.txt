Quadratic Spline
================

Functionality
-------------

This node generates a single section of quadratic Bezier spline. To generate a quadratic spline, you have to provide two end points ("knots") and one control point ("handle").

Inputs
------

This node has the following inputs:

- **Divisions**. Number of vertices to generate. Default value is 10.
- **Knot 1**. The beginning point of the curve.
- **Knot 2**. The ending point of the curve.
- **Handle**. The control point for the curve.

Parameters
----------

This node does not have specific parameters.

Outputs
-------

This node has the following outputs:

- **Verts**. Curve vertices.
- **Edges**. Curve edges.
- **ControlVerts**. Control vertices that define the curve. This output contains vertices from **Knot 1**, **Handle** and **Knot 2** inputs.
- **ControlEdges**. Edges that connect control vertices.

**ControlVerts** and **ControlEdges** outputs are useful mainly for debug visualization purposes.

Examples of Usage
-----------------

Simple example:

.. image:: https://user-images.githubusercontent.com/284644/67594672-4eb5fb80-f77e-11e9-8b1c-ad9689349ca7.png

Vectorization example:

.. image:: https://user-images.githubusercontent.com/284644/67594673-4f4e9200-f77e-11e9-8fba-daf74251ac00.png

