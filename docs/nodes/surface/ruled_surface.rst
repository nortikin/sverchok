Ruled Surface
==============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/bd6cfae6-1cdd-4e7f-a756-007da90b9d2d
  :target: https://github.com/nortikin/sverchok/assets/14288520/bd6cfae6-1cdd-4e7f-a756-007da90b9d2d

Functionality
-------------

This node generates a Surface as a linear interpolation of two Curve objects.
Such surface is widely known as a ruled surface, or a linear surface.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/36c2a604-b6ac-4150-8c2f-114d09769df4
  :target: https://github.com/nortikin/sverchok/assets/14288520/36c2a604-b6ac-4150-8c2f-114d09769df4

Along U parameter, such surface forms a curve calculated as a linear interpolation of two curves.
Along V parameter, such surface is always a straight line.

Surface domain: In U direction - from 0 to 1. In V direction - defined by node inputs, by default from 0 to 1. V = 0 corresponds to the first curve; V = 1 corresponds to the second curve.

Inputs
------

This node has the following inputs:

* **Curve1**. The first curve to interpolate. This input is mandatory.
* **Curve2**. The second curve to interpolate. This input is mandatory.
* **VMin**. The minimum value of curve V parameter. The default value is 0.
* **VMax**. The maximum value of curve V parameter. The default value is 1.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/7727a740-a299-4a11-a8bd-ca504c4fedce
      :target: https://github.com/nortikin/sverchok/assets/14288520/7727a740-a299-4a11-a8bd-ca504c4fedce

Parameters
----------

This node has the following parameter:

* **Native**. This parameter is available in the N panel only. If checked, then
  the node will try to use specific implementation of the ruled surface for
  cases when it is available. For example, if two curves provided are NURBS
  curves of equal degree, then the node will produce a NURBS surface. When not
  checked, or there is no specific implementation for provided curves, a
  generic algorithm will be used In most cases, the only visible difference is
  that the resulting surface can have different parametrization depending on
  this parameter. Also this parameter can be important if you wish to save the
  resulting surface into some file format that understands NURBS, or for Python
  API usage. Checked by default.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/407888a3-296a-4ec0-9e4b-86e7cfe4f59e
      :target: https://github.com/nortikin/sverchok/assets/14288520/407888a3-296a-4ec0-9e4b-86e7cfe4f59e


Outputs
-------

This node has the following output:

* **Surface**. The generated surface.

Examples of usage
-----------------



Generate a linear surface between a triangle and a hexagon:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/b3bb010e-617d-4fa6-97b5-dc690bc0f4d3
  :target: https://github.com/nortikin/sverchok/assets/14288520/b3bb010e-617d-4fa6-97b5-dc690bc0f4d3

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Curves->Curve Primitives-> :doc:`Polyline </nodes/curve/polyline>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`

Generate a linear surface between two cubic splines:

.. image:: https://user-images.githubusercontent.com/284644/79353383-6cf1fc80-7f54-11ea-855b-ec782edf2c5f.png
  :target: https://user-images.githubusercontent.com/284644/79353383-6cf1fc80-7f54-11ea-855b-ec782edf2c5f.png

* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`