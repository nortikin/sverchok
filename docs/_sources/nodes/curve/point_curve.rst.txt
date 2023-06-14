Single-Point Curve
==================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/d5612c79-047f-462f-9aac-cd758a47114d
  :target: https://github.com/nortikin/sverchok/assets/14288520/d5612c79-047f-462f-9aac-cd758a47114d

Functionality
-------------

This node generates a trivial curve, which consists of only one point in 3D
space. Such a curve is not useful by itself, but it can be useful in
combination with nodes which use curves to make some more complex construction.
For example, it is possible to do a loft with a single-point curve.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/a95e129c-81bf-490d-b722-d58bf1cf100f
  :target: https://github.com/nortikin/sverchok/assets/14288520/a95e129c-81bf-490d-b722-d58bf1cf100f

* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
 
Inputs
------

This node has the following input:

* **Point**. The point which will become the Curve object. The default value is (0, 0, 0).

Parameters
----------

This node does not have parameters.

Outputs
-------

This node has the following output:

* **Curve**. The generated Curve object.

Examples of Usage
-----------------

Use with "Blend Curves" node to construct a smooth continuation of given curve, which ends in a specific point:

.. image:: https://user-images.githubusercontent.com/284644/210247639-1352bd93-10a4-4145-97de-2f770afa368a.png
  :target: https://user-images.githubusercontent.com/284644/210247639-1352bd93-10a4-4145-97de-2f770afa368a.png

* Curves-> :doc:`Blend Curves </nodes/curve/blend_curves>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`

Use with "NURBS Loft" node, to construct a surface which has "poles":

.. image:: https://user-images.githubusercontent.com/284644/210247716-70957dc2-6495-4067-ae1f-6ae0f0c3e9b9.png
  :target: https://user-images.githubusercontent.com/284644/210247716-70957dc2-6495-4067-ae1f-6ae0f0c3e9b9.png

* Curves-> :doc:`Bezier Spline Segment (Curve) </nodes/curve/bezier_spline>`
* Surfaces-> :doc:`NURBS Loft </nodes/surface/nurbs_loft>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw Surface </nodes/viz/viewer_draw_surface>`