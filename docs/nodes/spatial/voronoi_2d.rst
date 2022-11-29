Voronoi 2D Node
===============

.. image:: https://user-images.githubusercontent.com/14288520/202251049-aea22f20-4e85-4f60-acff-9f2107f41a35.png
  :target: https://user-images.githubusercontent.com/14288520/202251049-aea22f20-4e85-4f60-acff-9f2107f41a35.png

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

* **Vertices**. Set of input vertices (sites) to build Voronoi diagram for.
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

.. image:: https://user-images.githubusercontent.com/14288520/202302819-11154af6-a7ba-41e4-ae22-a7f29caf356a.gif
  :target: https://user-images.githubusercontent.com/14288520/202302819-11154af6-a7ba-41e4-ae22-a7f29caf356a.gif

- **Draw Tails**. If checked, then the edges that go from the central part of
  diagram to outside the bounding line, will be generated. This parameter is
  available only if **Draw Bounds** is not checked. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/202302012-eeae6d5d-eeba-4085-ad42-024f9d62b14a.gif
  :target: https://user-images.githubusercontent.com/14288520/202302012-eeae6d5d-eeba-4085-ad42-024f9d62b14a.gif

- **Clipping**. Amount of space to be added for bounding line. If bounds are
  defined by bounding box, then this amount of space will be added in each
  direction (top, bottom, right and left). If bounds are defined by bounding
  circle, then this amount will be added to the circle's radius. Default value is 1.0.

.. image:: https://user-images.githubusercontent.com/14288520/202301245-290645f8-e54c-45da-b158-5e6eb5c17dce.gif
  :target: https://user-images.githubusercontent.com/14288520/202301245-290645f8-e54c-45da-b158-5e6eb5c17dce.gif

- **Make Faces**. If checked, then "fill holes" function will be used to create
  polygons of the Voronoi diagram. Maximum number of polygon sides is
  controlled by the **MaxSides** input / parameter. Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/202297472-63ba8e87-5fb8-4348-a60b-3b0e8f747736.gif
  :target: https://user-images.githubusercontent.com/14288520/202297472-63ba8e87-5fb8-4348-a60b-3b0e8f747736.gif

- **Ordered faces**. This parameter is available in the N palen only, and only
  if **Make Faces** parameter is checked. If enabled, the node will make sure
  that generated faces are in the same order as input vertices. This procedure
  can take additional time. If not checked, the order of faces will not be the
  same as order of initial points.

.. image:: https://user-images.githubusercontent.com/14288520/202300322-bfa83fa1-2f19-46cc-a462-f47cc21a4d08.gif
  :target: https://user-images.githubusercontent.com/14288520/202300322-bfa83fa1-2f19-46cc-a462-f47cc21a4d08.gif

Outputs
-------

This node has the following outputs:

- **Vertices**
- **Edges**
- **Faces**. This output is available only if the **Make Faces** parameter is checked.

Examples of usage
-----------------

Simple example:

.. image:: https://user-images.githubusercontent.com/14288520/202290645-5c54af82-7ecc-4bc9-bd6d-c2d06d7d875d.png
  :target: https://user-images.githubusercontent.com/14288520/202290645-5c54af82-7ecc-4bc9-bd6d-c2d06d7d875d.png

Circular clipping:

.. image:: https://user-images.githubusercontent.com/14288520/202292894-4961f0d2-62c2-4062-af19-8a5b5d3ce07b.png
  :target: https://user-images.githubusercontent.com/14288520/202292894-4961f0d2-62c2-4062-af19-8a5b5d3ce07b.png

.. image:: https://user-images.githubusercontent.com/14288520/202293847-815df87d-b861-4416-82ef-70184e55c102.png
  :target: https://user-images.githubusercontent.com/14288520/202293847-815df87d-b861-4416-82ef-70184e55c102.png

