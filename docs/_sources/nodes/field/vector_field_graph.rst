Vector Field Graph
==================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/25cf4c3e-1bd0-4d81-94f4-ede174133db5
  :target: https://github.com/nortikin/sverchok/assets/14288520/25cf4c3e-1bd0-4d81-94f4-ede174133db5

Functionality
-------------

This node visualizes a Vector Field object by generating arrows (which
represent vectors) from points of original space to the results of vector field
application to those original points.

The original points are generated as cartesian grid in 3D space.

This node is mainly intended for visualization.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/9a50d9d4-b02e-4b28-9412-c32c4a0c9325
  :target: https://github.com/nortikin/sverchok/assets/14288520/9a50d9d4-b02e-4b28-9412-c32c4a0c9325

Inputs
------

This node has the following inputs:

* **Field**. The vector field to be visualized. This input is mandatory.
* **Bounds**. The list of points which define the area of space, in which the
  field is to be visualized. Only the bounding box of these points is used.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/7f70ce5f-9863-4ea9-a951-e4d662904ff0
      :target: https://github.com/nortikin/sverchok/assets/14288520/7f70ce5f-9863-4ea9-a951-e4d662904ff0

* **Scale**. The scale of arrows to be generated. The default value is 1.0.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/a22b74c7-1d2d-4ca9-89a7-6f90a02e72a1
      :target: https://github.com/nortikin/sverchok/assets/14288520/a22b74c7-1d2d-4ca9-89a7-6f90a02e72a1

* **SamplesX**, **SamplesY**, **SamplesZ**. The number of samples of cartesian
  grid, from which the arrows are to be generated. The default value is 10.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c87e10e5-9746-4246-8542-ee7f73231aa8
      :target: https://github.com/nortikin/sverchok/assets/14288520/c87e10e5-9746-4246-8542-ee7f73231aa8

Parameters
----------

This node has the following parameters:

* **Auto scale**. Select the scale of arrows automatically, so that the largest
  arrows are not bigger than the distance between cartesian grid points.
  Checked by default.
* **Join**. If checked, then all arrows will be merged into one mesh object.
  Otherwise, separate object will be generated for each arrow. Checked by
  default.

Outputs
-------

Example of description:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/18376fca-ba21-4d46-8c44-f7f019da86a7
  :target: https://github.com/nortikin/sverchok/assets/14288520/18376fca-ba21-4d46-8c44-f7f019da86a7

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Fields-> :doc:`Voronoi Field </nodes/field/voronoi_field>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

This node has the following outputs:

* **Vertices**. The vertices of the arrows.
* **Edges**. The edges of the arrows.

Example of usage
----------------

Visualize some vector field:

.. image:: https://user-images.githubusercontent.com/284644/79471192-b8bba900-801b-11ea-829e-2b003d9000da.png
  :target: https://user-images.githubusercontent.com/284644/79471192-b8bba900-801b-11ea-829e-2b003d9000da.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`