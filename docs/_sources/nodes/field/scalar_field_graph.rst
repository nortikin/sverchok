Scalar Field Graph
==================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/5294a47c-7cdb-4481-9672-e72e1d8f0038
  :target: https://github.com/nortikin/sverchok/assets/14288520/5294a47c-7cdb-4481-9672-e72e1d8f0038

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

.. image:: https://github.com/nortikin/sverchok/assets/14288520/1cd5d9ad-cb5f-46a5-9b9b-6cbf0f0c8d55
  :target: https://github.com/nortikin/sverchok/assets/14288520/1cd5d9ad-cb5f-46a5-9b9b-6cbf0f0c8d55

See also
--------

* Curves-> :doc:`Marching Squares </nodes/curve/marching_squares>`

Inputs
------

This node has the following inputs:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/de60a767-1261-4f5d-8873-1672d29c48ed
  :target: https://github.com/nortikin/sverchok/assets/14288520/de60a767-1261-4f5d-8873-1672d29c48ed

* **Field**. Scalar field to be visualized. This input is mandatory.
* **Bounds**. Set of vertices that define the bounding box where the graph will
  be generated. Exact vertices are not used, only their bounding box is used.
  This input is mandatory.
* **SamplesXY**. Number of samples (resolution) along X and Y coordinates. The
  default value is 50.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/495e6f54-572d-4198-a622-bbc1d2d1d1b4
      :target: https://github.com/nortikin/sverchok/assets/14288520/495e6f54-572d-4198-a622-bbc1d2d1d1b4

* **SamplesZ**. Number of samples along Z coordinates, i.e. the number of
  planes to draw iso-lines on. The default value is 10.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/d76b04d2-eb18-4399-b66d-61e2a5e5baf4
      :target: https://github.com/nortikin/sverchok/assets/14288520/d76b04d2-eb18-4399-b66d-61e2a5e5baf4

* **ValueSamples**. Number of different values used as iso-values. This defines
  the number of contours which are drawn on each plane. The default value is
  10.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/d017c223-9ec8-4d07-8924-f85f1409fd24
      :target: https://github.com/nortikin/sverchok/assets/14288520/d017c223-9ec8-4d07-8924-f85f1409fd24

Parameters
----------

This node has the following parameters:

* **Make faces**. If checked, the node will generate a face for each closed
  contour. Unchecked by default.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/5a5c476f-52c3-430c-937c-2d9097aa7e8d
      :target: https://github.com/nortikin/sverchok/assets/14288520/5a5c476f-52c3-430c-937c-2d9097aa7e8d

* **Connect boundary**. If checked, the node will connect pieces of the same
  curve, that was split because it was cut by specified X/Y bounds. Otherwise,
  several separate pieces will be generated in such case. Unchecked by default.
  (Connected only one split in one axis. If contour has more one split - no connection)

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/0c200673-e093-4f1d-aa63-54d3bdc710f3
      :target: https://github.com/nortikin/sverchok/assets/14288520/0c200673-e093-4f1d-aa63-54d3bdc710f3

* **Join**. If checked, then the node will join all generated contours for each
  field into one mesh object. Otherwise, the node will output a separate mesh
  object for each contour. Checked by default.
  You can colorize them for example.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/19476719-4e4b-4f42-a846-8b3add547578
      :target: https://github.com/nortikin/sverchok/assets/14288520/19476719-4e4b-4f42-a846-8b3add547578

Outputs
-------

This node has the following outputs:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/a6210ddf-9a2c-4f62-b08c-fee2429b71e2
  :target: https://github.com/nortikin/sverchok/assets/14288520/a6210ddf-9a2c-4f62-b08c-fee2429b71e2

* **Vertices**. Vertices of the generated contours.
* **Edges**. Edges of the generated contours.
* **Faces**. Faces made for closed contours. This output is only available when
  the **Make faces** parameter is checked.

Some results are weird:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/7b2a1a3d-3302-40e2-ae87-11b8f6f39a0e
  :target: https://github.com/nortikin/sverchok/assets/14288520/7b2a1a3d-3302-40e2-ae87-11b8f6f39a0e

Example of usage
----------------

Example of description:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/7adad2bf-0c83-4e32-b99d-e9265fb361b0
  :target: https://github.com/nortikin/sverchok/assets/14288520/7adad2bf-0c83-4e32-b99d-e9265fb361b0

* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`

---------

.. image:: https://user-images.githubusercontent.com/284644/87240609-59134500-c434-11ea-9eb3-5a43420ff2cf.png
  :target: https://user-images.githubusercontent.com/284644/87240609-59134500-c434-11ea-9eb3-5a43420ff2cf.png

* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`