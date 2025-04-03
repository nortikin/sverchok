Quadratic Spline
================

.. image:: https://user-images.githubusercontent.com/14288520/188749135-04deebda-04b6-4a20-bad6-96eb96d4ecec.png
  :target: https://user-images.githubusercontent.com/14288520/188749135-04deebda-04b6-4a20-bad6-96eb96d4ecec.png

Functionality
-------------

This node generates a single section of quadratic Bezier spline. To generate a quadratic spline, you have to provide two end points ("knots") and one control point ("handle").

Inputs
------

This node has the following inputs:

- **Num Verts**. Number of vertices to generate. Default value is 10.
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

.. image:: https://user-images.githubusercontent.com/14288520/188751459-e155c353-7ebe-42e5-9c81-206061ab24ec.png
    :target: https://user-images.githubusercontent.com/14288520/188751459-e155c353-7ebe-42e5-9c81-206061ab24ec.png

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Vectorization example:

.. image:: https://user-images.githubusercontent.com/14288520/188752243-5e09bde9-3af0-488e-868d-8603e246b7b7.png
    :target: https://user-images.githubusercontent.com/14288520/188752243-5e09bde9-3af0-488e-868d-8603e246b7b7.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`