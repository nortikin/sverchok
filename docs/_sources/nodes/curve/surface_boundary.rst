Surface's Boundary
==================

.. image:: https://user-images.githubusercontent.com/14288520/211388504-d688ddff-0ba8-41ec-a674-74ad7dc45040.png
  :target: https://user-images.githubusercontent.com/14288520/211388504-d688ddff-0ba8-41ec-a674-74ad7dc45040.png

Functionality
-------------

This node outputs the curve (or curves) which represent the boundaries of some surface. The supported types of surfaces are:

* Plain (plane-like); for such surfaces, the boundary is one closed curve (in
  many cases it will have four non-smooth points).
* Closed in U or in V direction (cylinder-like). For such surface, the boundary
  is represented by two closed curves at two open sides of the surface.

If the surface is closed in both U and V direction (torus-like), then it will not have any boundary.

.. image:: https://user-images.githubusercontent.com/14288520/211390865-1e54510c-969a-4545-800a-0231b55fa8dd.png
  :target: https://user-images.githubusercontent.com/14288520/211390865-1e54510c-969a-4545-800a-0231b55fa8dd.png

Inputs
------

This node has the following input:

* **Surface**. The surface to calculate boundary for. This input is mandatory.

Parameters
----------

This node has the following parameters:

* **Cyclic**. This defines whether the surface is closed in some directions. The available options are:

  * **Plain**. The surface is not closed in any direction, so it has single closed curve as a boundary.

  .. image:: https://user-images.githubusercontent.com/14288520/211394815-fbe51d8d-b182-4b2c-b89b-7f60c5299d2b.png
    :target: https://user-images.githubusercontent.com/14288520/211394815-fbe51d8d-b182-4b2c-b89b-7f60c5299d2b.png

  * **U Cyclic**. The surface is closed along the U direction. It has two closed curves as boundary.
  
  .. image:: https://user-images.githubusercontent.com/14288520/211395429-de1cec75-f633-4fb2-9cb2-94288584617c.png
    :target: https://user-images.githubusercontent.com/14288520/211395429-de1cec75-f633-4fb2-9cb2-94288584617c.png

  * **V Cyclic**. The surface is closed along the V direction.

  .. image:: https://user-images.githubusercontent.com/14288520/211395853-0ce0f227-da33-41f3-86fe-936054021da5.png
    :target: https://user-images.githubusercontent.com/14288520/211395853-0ce0f227-da33-41f3-86fe-936054021da5.png

* **Concatenate**. This parameter is available only if **Cyclic** parameter is
  set to **Plain**. If checked, then four edges of the surface will be
  concatenated into one Curve object. Otherwise, the node will output four
  separate Curve objects. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/211396496-ff819f75-6254-48d7-86a5-15d310062ebd.png
  :target: https://user-images.githubusercontent.com/14288520/211396496-ff819f75-6254-48d7-86a5-15d310062ebd.png

Outputs
-------

This node has the following output:

* **Boundary**. Curve or curves representing surface's boundary.

Examples of usage
-----------------

Visualize the boundary of some random plane-like surface:

.. image:: https://user-images.githubusercontent.com/284644/78506070-b8581e00-7790-11ea-9af1-2c3c84264dc8.png
  :target: https://user-images.githubusercontent.com/284644/78506070-b8581e00-7790-11ea-9af1-2c3c84264dc8.png

replay with new nodes:

.. image:: https://user-images.githubusercontent.com/14288520/211398183-1acee1d4-ca57-4e0d-bc04-20d5a0feacdd.png
  :target: https://user-images.githubusercontent.com/14288520/211398183-1acee1d4-ca57-4e0d-bc04-20d5a0feacdd.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Surfaces-> :doc:`Surface from Curves </nodes/surface/interpolating_surface>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* List->List Struct-> :doc:`List Split </nodes/list_struct/split>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Visualize the boundary of cylinder-like surface:

.. image:: https://user-images.githubusercontent.com/14288520/211399221-75994afc-4a1a-41b5-8092-b3cbd30a1efd.png
  :target: https://user-images.githubusercontent.com/14288520/211399221-75994afc-4a1a-41b5-8092-b3cbd30a1efd.png

* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Surfaces-> :doc:`Extrude Curve Along Vector </nodes/surface/extrude_vector>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`