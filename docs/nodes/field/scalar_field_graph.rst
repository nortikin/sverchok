Scalar Field Graph
==================

Dependencies
------------

This node requires SkImage_ library to work.

.. _SkImage: https://scikit-image.org/

Functionality
-------------

This node uses Marching Squares_ algorithm to generate iso-lines of a given
scalar field on a series of planes for a series of iso-values. This node is
mainly intended for visualization of scalar fields, but may be useful for other
things too.

.. _Squares: https://en.wikipedia.org/wiki/Marching_squares

Inputs
------

This node has the following inputs:

* **Field**. Scalar field to be visualized. This input is mandatory.
* **Bounds**. Set of vertices that define the bounding box where the graph will
  be generated. Exact vertices are not used, only their bounding box is used.
  This input is mandatory.
* **SamplesXY**. Number of samples (resolution) along X and Y coordinates. The
  default value is 50.
* **SamplesZ**. Number of samples along Z coordinates, i.e. the number of
  planes to draw iso-lines on. The default value is 10.
* **ValueSamples**. Number of different values used as iso-values. This defines
  the number of contours which are drawn on each plane. The default value is
  10.

Parameters
----------

This node has the following parameters:

* **Make faces**. If checked, the node will generate a face for each closed
  contour. Unchecked by default.
* **Counnect boundary**. If checked, the node will connect pieces of the same
  curve, that was split because it was cut by specified X/Y bounds. Otherwise,
  several separate pieces will be generated in such case. Unchecked by default.
* **Join**. If checked, then the node will join all generated contours for each
  field into one mesh object. Otherwise, the node will output a separate mesh
  object for each contour. Checked by default.

Outputs
-------

This node has the following outputs:

* **Vertices**. Vertices of the generated contours.
* **Edges**. Edges of the generated contours.
* **Faces**. Faces made for closed contours. This output is only available when
  the **Make faces** parameter is checked.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/87240609-59134500-c434-11ea-9eb3-5a43420ff2cf.png

