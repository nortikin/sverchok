Surface Lerp
============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/15c887c8-cc1c-4fb6-9b38-1f2774ebe9a2
  :target: https://github.com/nortikin/sverchok/assets/14288520/15c887c8-cc1c-4fb6-9b38-1f2774ebe9a2

Functionality
-------------

This node generates a Surface by calculating the linear interpolation ("lerp") between two other Surfaces.

Surface domain: from 0 to 1 in both directions.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/72e350ab-38ca-429a-8a4a-e82d1325bf2e
  :target: https://github.com/nortikin/sverchok/assets/14288520/72e350ab-38ca-429a-8a4a-e82d1325bf2e

Inputs
------

This node has the following inputs:

* **Surface1**. The first surface for the interpolation. This input is mandatory.
* **Surface2**. The second surface for the interpolation. This input is mandatory.
* **Coefficient**. Interpolation coefficient. Value of 0 will generate the
  surface equivalent to Surface1. Value of 1 will generate the surface
  equivalent to Surface2. The default value is 0.5 (in the middle of two
  surfaces).

Outputs
-------

This node has the following output:

   * **Surface**. The interpolated surface.

Example of usage
----------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/fb86952d-9d59-4929-85e0-d77ce26b3df2
  :target: https://github.com/nortikin/sverchok/assets/14288520/fb86952d-9d59-4929-85e0-d77ce26b3df2

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Surfaces-> :doc:`Minimal Surface </nodes/surface/minimal_surface>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Interpolation of some random surfaces:

.. image:: https://user-images.githubusercontent.com/284644/79361263-7f713380-7f5e-11ea-89de-60c74c4e1594.png
  :target: https://user-images.githubusercontent.com/284644/79361263-7f713380-7f5e-11ea-89de-60c74c4e1594.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Surfaces-> :doc:`Extrude Curve Along Curve </nodes/surface/extrude_curve>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`