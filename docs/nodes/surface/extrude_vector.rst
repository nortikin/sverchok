Extrude Curve Along Vector
==========================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/22dcccc0-24d3-4e74-997f-fc5e5b2bcdef
  :target: https://github.com/nortikin/sverchok/assets/14288520/22dcccc0-24d3-4e74-997f-fc5e5b2bcdef

Functionality
-------------

This node generates a Surface by extruding a Curve (called "profile") along some vector.

Surface domain: along U direction - the same as of profile curve; along V
direction - from 0 to 1. V = 0 corresponds to the initial position of profile
curve.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/89208607-97fd-4391-849e-6a1e3ae8c543
  :target: https://github.com/nortikin/sverchok/assets/14288520/89208607-97fd-4391-849e-6a1e3ae8c543

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Curves->Curve Primitives-> :doc:`Fillet Polyline </nodes/curve/fillet_polyline>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Inputs
------

This node has the following inputs:

* **Profile**. The curve to be extruded. This input is mandatory.
* **Vector**. The vector along which the curve must be extruded. The default value is `(0, 0, 1)`.

Outputs
-------

This node has the following output:

* **Surface**. The generated surface.

Example of usage
----------------

Extrude some cubic spline along a vector:

.. image:: https://user-images.githubusercontent.com/284644/79358827-2ce24800-7f5b-11ea-91ec-a5df4762e610.png
  :target: https://user-images.githubusercontent.com/284644/79358827-2ce24800-7f5b-11ea-91ec-a5df4762e610.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
