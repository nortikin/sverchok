Vector Field Graph
==================

Functionality
-------------

This node visualizes a Vector Field object by generating arrows (which
represent vectors) from points of original space to the results of vector field
application to those original points.

The original points are generated as carthesian grid in 3D space.

This node is mainly intended for visualization.

Inputs
------

This node has the following inputs:

* **Field**. The vector field to be visualized. This input is mandatory.
* **Bounds**. The list of points which define the area of space, in which the
  field is to be visualized. Only the bounding box of these points is used.
* **Scale**. The scale of arrows to be generated. The default value is 1.0.
* **SamplesX**, **SamplesY**, **SamplesZ**. The number of samples of carthesian
  grid, from which the arrows are to be generated. The default value is 10.

Parameters
----------

This node has the following parameters:

* **Auto scale**. Select the scale of arrows automatically, so that the largest
  arrows are not bigger than the distance between carthesian grid points.
  Checked by default.
* **Join**. If checked, then all arrows will be merged into one mesh object.
  Otherwise, separate object will be generated for each arrow. Checked by
  default.

Outputs
-------

This node has the following outputs:

* **Vertices**. The vertices of the arrows.
* **Edges**. The edges of the arrows.

Example of usage
----------------

Visualize some vector field:

.. image:: https://user-images.githubusercontent.com/284644/79471192-b8bba900-801b-11ea-829e-2b003d9000da.png

