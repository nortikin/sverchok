Curve Endpoints
===============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/cd2c2bcc-2d3d-4482-a82d-60d097d7df26
  :target: https://github.com/nortikin/sverchok/assets/14288520/cd2c2bcc-2d3d-4482-a82d-60d097d7df26

Functionality
-------------

This node outputs starting and ending points of the curve.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/b14902af-ec58-48ee-8d2e-e2265b48bc14
  :target: https://github.com/nortikin/sverchok/assets/14288520/b14902af-ec58-48ee-8d2e-e2265b48bc14

Note that for closed curves the start and the end point will coincide.

Inputs
------

This node has the following input:

* **Curve**. The curve to calculate endpoints of. This input is mandatory.

Outputs
-------

This node has the following outputs:

* **Start**. The starting point of the curve.
* **End**. The end point of the curve.

Example of usage
----------------

Visualize end points of some curve (old example):

.. image:: https://user-images.githubusercontent.com/284644/78505629-20593500-778e-11ea-998b-53b5b87925d3.png
  :target: https://user-images.githubusercontent.com/284644/78505629-20593500-778e-11ea-998b-53b5b87925d3.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Refactor of old example
-----------------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/d9d8cb0f-5517-4996-bfe2-d272d6a528f1
  :target: https://github.com/nortikin/sverchok/assets/14288520/d9d8cb0f-5517-4996-bfe2-d272d6a528f1

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`