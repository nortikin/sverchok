Voronoi 2D Node
===============

Functionality
-------------

This node generates Voronoi_ diagram for the provided set of vertices in 2D space (in XOY plane).

In general, Voronoi diagram is infinite construction that covers the whole XOY
plane. We cannot deal with such endless thing, so we have to clip that with
some bounds. It is possible to define bounds either based on bounding box of
provided vertices, or based on a circle that encloses all provided vertices.

When we clip the diagram, there can be clipped polygons (they are produced when
the bounding line splits the polygon from original diagram in two parts) or
clipped lines (because some lines in original Voronoi diagram are endless).

.. _Voronoi: https://en.wikipedia.org/wiki/Voronoi_diagram

Inputs
------

The node has the following inputs:

* **Vertices**. Set of input vertices to build Voronoi diagram for.
* **MaxSides**. Maximum number of sides of the output polygons. If the Voronoi
  diagram polygon will have more sides, then it will not be created. Default
  value is 10. This input is available only if **Make Faces** parameter is
  checked. The value can also be provided as a parameter.

Parameters
----------

This node has the following parameters:

- **Bounds Mode**. The mode of diagram bounds definition. Possible values are
  **Bounding Box** and **Circle**. The default value is **Bounding Box**.
- **Draw Bounds**. If checked, then the edges connecting boundary vertices will
  be generated. Checked by default.
- **Draw Tails**. If checked, then the edges that go from the central part of
  diagram to outside the bounding line, will be generated. This parameter is
  available only if **Draw Bounds** is not checked. Checked by default.
- **Clipping**. Amount of space to be added for bounding line. If bounds are
  defined by bounding box, then this amount of space will be added in each
  direction (top, bottom, right and left). If bounds are defined by bounding
  circle, then this amount will be added to the circle's radius. Default value is 1.0.
- **Make Faces**. If checked, then "fill holes" function will be used to create
  polygons of the Voronoi diagram. Maximum number of polygon sides is
  controlled by the **MaxSides** input / parameter. Unchecked by default.

Outputs
-------

This node has the following outputs:

- **Vertices**
- **Edges**
- **Faces**. This output is available only if the **Make Faces** parameter is checked.

Examples of usage
-----------------

Simple example:

.. image:: https://user-images.githubusercontent.com/284644/67318730-4a42d600-f525-11e9-88bf-1ec882cfdb2e.png

Circular clipping:

.. image:: https://user-images.githubusercontent.com/284644/67318729-4a42d600-f525-11e9-9909-2dce4218f89b.png

.. image:: https://user-images.githubusercontent.com/284644/67318728-4a42d600-f525-11e9-961c-26f2f72e749a.png

