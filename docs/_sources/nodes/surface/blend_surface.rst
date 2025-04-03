Blend Surfaces
==============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/bcf0b3bd-b7df-40e7-beef-20a048056753
  :target: https://github.com/nortikin/sverchok/assets/14288520/bcf0b3bd-b7df-40e7-beef-20a048056753

Functionality
-------------

This node generates a Surface, which creates a smooth blend between two other
surfaces. It is possible to select which edges of surfaces must be blended.
Also it is possible to provide arbitrary curves in U/V space of each surface,
along which the blending surface must start and end.

Surface domain: from 0 to 1 in both directions.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/95aa08e7-5931-4133-b9b3-e9d9060e37a8
  :target: https://github.com/nortikin/sverchok/assets/14288520/95aa08e7-5931-4133-b9b3-e9d9060e37a8

* Surfaces-> :doc:`Surface Domain </nodes/surface/surface_domain>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`

Inputs
------

This node has the following inputs:

* **Surface1**. The first surface to make a blend with. This input is mandatory.
* **UVCurve1**. A curve in U/V space of the first surface, along which the
  blending surface must start. This input is available and mandatory only when
  **Curve1** parameter is set to **Custom**.
* **Bulge1**. Bulge factor for the place where the blending surface touches the
  first surface. Bigger values lead to more smooth touch. Negative values will
  mean that the blending surface will touch the surface from another side of
  curve / edge. The default value is 1.0.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/1a293c38-ce99-4bdf-9213-8074b9f92dba
      :target: https://github.com/nortikin/sverchok/assets/14288520/1a293c38-ce99-4bdf-9213-8074b9f92dba

* **Surface2**. The second surface to make a blend with. This input is mandatory.
* **UVCurve2**. A curve in U/V space of the second surface, along which the
  blending surface must end. This input is available and mandatory only when
  **Curve2** parameter is set to **Custom**.
* **Bulge2**. Bulge factor for the place where the blending surface touches the
  second surface. Bigger values lead to more smooth touch. Negative values will
  mean that the blending surface will touch the surface from another side of
  curve / edge. The default value is 1.0.
* **Samples**. This input is available only when the **NURBS** parameter is
  checked. This defines the number of points used to approximate initial
  (touching) curves with NURBS curves. The default value is 10. Greater values
  mean better approximation, but worse performance.

Parameters
----------

This node has the following parameters:

* **Smoothness**. This defines how smooth the connection between initial
  surfaces and generated blending surface should be. The available options are:

  * **G1 - Tangency**. Exact matching of tangents is guaranteed.
    
    .. image:: https://user-images.githubusercontent.com/284644/210866314-f05d511e-8ae9-46aa-88b1-feb030c67ce1.png
      :target: https://user-images.githubusercontent.com/284644/210866314-f05d511e-8ae9-46aa-88b1-feb030c67ce1.png

  * **G2 - Curvature**. Matching of geometric curvature is guaranteed.

    .. image:: https://user-images.githubusercontent.com/284644/210866466-2a0d5628-0d00-48ad-a28b-5c037d84b7fd.png
      :target: https://user-images.githubusercontent.com/284644/210866466-2a0d5628-0d00-48ad-a28b-5c037d84b7fd.png

   The default option is **G1 - Tangency**.

* **Curve1**. This defines where the blending surface should touch the first surface. The available options are:

  * **Min U**. Use the edge of the surface with the minimum value of U parameter.
  * **Max U**. Use the edge of the surface with the maximum value of U parameter.
  * **Min V**. Use the edge of the surface with the minimum value of V parameter.
  * **Max V**. Use the edge of the surface with the maximum value of V parameter.
  * **Custom**. Use arbitrary curve in the surface's U/V space, which is
    provided in the **UVCurve1** input.

  The default value is **Min U**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/3b0a950a-2121-4d07-a3c1-e6b8920a0dd8
      :target: https://github.com/nortikin/sverchok/assets/14288520/3b0a950a-2121-4d07-a3c1-e6b8920a0dd8


* **Flip Curve 1**. If checked, the direction of curve (or edge), where the
  blending surface touches the first surface, will be reversed. Unchecked by
  default.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/704c40e6-4195-41d1-a069-3993328d438e
      :target: https://github.com/nortikin/sverchok/assets/14288520/704c40e6-4195-41d1-a069-3993328d438e

* **Curve2**. This defines where the blending surface should touch the second
  surface. The available options are the same as for **Curve1** parameter. The
  default value is **Min U**.
* **Flip Curve 2**. If checked, the direction of curve (or edge), where the
  blending surface touches the second surface, will be reversed. Unchecked by
  default. (See pic. *Flip Curve 1*)
* **NURBS**. If checked, the node will generate a NURBS surface instead of
  generic surface object. The NURBS surface only approximates the ideal
  blending surface. It is constructed as a Gordon surface, by approximating the
  two initial curves with NURBS curves. The number of points used for
  approximation is controlled by **Samples** input. Unchecked by default.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c3406dd7-32b9-407b-931b-5ccfc632741f
      :target: https://github.com/nortikin/sverchok/assets/14288520/c3406dd7-32b9-407b-931b-5ccfc632741f

Outputs
-------

This node has the following output:

* **Surface**. The generated blending surface.

Examples of usage
-----------------

A simple example. Make two planar patches and make a blending surface, which touches them at the edges:

.. image:: https://user-images.githubusercontent.com/284644/89387742-5b5b7d00-d71c-11ea-929c-43083ab34774.png
  :target: https://user-images.githubusercontent.com/284644/89387742-5b5b7d00-d71c-11ea-929c-43083ab34774.png

* Surfaces-> :doc:`Plane (Surface) </nodes/surface/plane>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`


More complex example. Similar, but for one of the patches define a circular arc
in it's U/V space, and make the blending surface touch this plane along that
circular arc:

.. image:: https://user-images.githubusercontent.com/284644/89387738-5a2a5000-d71c-11ea-9018-4d62f6eb464f.png
  :target: https://user-images.githubusercontent.com/284644/89387738-5a2a5000-d71c-11ea-9018-4d62f6eb464f.png

* Curves-> :doc:`Curve Formula </nodes/curve/curve_formula>`
* Surfaces-> :doc:`Plane (Surface) </nodes/surface/plane>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

An example of NURBS mode:

.. image:: https://user-images.githubusercontent.com/284644/209392203-c9da3a3f-5a5b-469c-8a8b-0afda3f5f176.png
  :target: https://user-images.githubusercontent.com/284644/209392203-c9da3a3f-5a5b-469c-8a8b-0afda3f5f176.png

* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* Surfaces-> :doc:`Plane (Surface) </nodes/surface/plane>`
* Surfaces-> :doc:`Apply Field to Surface </nodes/surface/apply_field_to_surface>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw Surface </nodes/viz/viewer_draw_surface>`
