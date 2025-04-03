Surface from Boundary Curves
============================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/6cc29a29-f4bb-41e2-b507-90a55e08ae21
  :target: https://github.com/nortikin/sverchok/assets/14288520/6cc29a29-f4bb-41e2-b507-90a55e08ae21

Functionality
-------------

This node generates a Surface object from exactly four Curve object, that
define the boundary of the surface. For example, it can build a plane square
from four edges of that square.

It is assumed that curves provided have the following properties:

* They meet exactly at the corner points of the surface.
* Their directions are orgainized so that the four curves build a cycle (either
  clockwise or counterclockwise).

.. image:: https://github.com/nortikin/sverchok/assets/14288520/57833c0e-4bad-47dc-87b7-4d8c78de1220
  :target: https://github.com/nortikin/sverchok/assets/14288520/57833c0e-4bad-47dc-87b7-4d8c78de1220

That is, the second curve must begin at the point where the first curve ends;
and the third curve must begin at the point where the second curve ends; and so
on.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/b7c01c67-6639-4a14-8810-51a0ed6aec76
  :target: https://github.com/nortikin/sverchok/assets/14288520/b7c01c67-6639-4a14-8810-51a0ed6aec76

It is also possible to omit the fourth curve, thus to build a surface from
three boundary curves. If the third curve does not end in the same point where
the first curve started, the node will use a straight line segment as fourth
curve.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/b042b7ff-04eb-4aba-a1d9-72d52b1a8c88
  :target: https://github.com/nortikin/sverchok/assets/14288520/b042b7ff-04eb-4aba-a1d9-72d52b1a8c88

The surface is calculated as a Coons patch, see https://en.wikipedia.org/wiki/Coons_patch.

When all provided curves are NURBS or NURBS-like, then the node will try to
output NURBS surface. The sufficient requirement for this is that opposite
curves have equal degree. If it is not possible to make a NURBS surface, the
node will create a generic Coons surface.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e85b9590-a592-4cdc-b0d7-7be857be2ded
  :target: https://github.com/nortikin/sverchok/assets/14288520/e85b9590-a592-4cdc-b0d7-7be857be2ded

Surface domain: from 0 to 1 in both directions.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/f2bf30dd-ca83-485a-bdc1-3521e1426d9b
  :target: https://github.com/nortikin/sverchok/assets/14288520/f2bf30dd-ca83-485a-bdc1-3521e1426d9b

Inputs
------

This node has the following inputs:

* **Curves**. The list of curves to build a surface form. This input can accept
  data with nesting level of 1 or 2 (list of curves or list of lists of
  curves). Each list of curves must have length of 3 or 4. This input is available
  and mandatory only if **Input** parameter is set to **List of Curves**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c610ba43-0628-48da-b1d1-f84831fb1509
      :target: https://github.com/nortikin/sverchok/assets/14288520/c610ba43-0628-48da-b1d1-f84831fb1509

* **Curve1**, **Curve2**, **Curve3**, **Curve4**. Curves to build surface from.
  These inputs can accept data with nesting level 1 only (list of curves).
  These inputs are available only if **Input** parameter is set
  to **4 Curves**. Inputs **Curve1**, **Curve2** and **Curve3** are mandatory.
  **Curve4** input is optional.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/318f24d4-03eb-4fb7-a3a6-496066b2d648
      :target: https://github.com/nortikin/sverchok/assets/14288520/318f24d4-03eb-4fb7-a3a6-496066b2d648

Parameters
----------

This node has the following parameters:

* **Input**. This defines how the curves are provided. The following options are available:

  * **List of curves**. All curves are provided in a single input **Curves**.
  * **Separate inputs**. Each curve is provided in separate input **Curve1** - **Curve4**.

  The default value is **List of Curves**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/468bf917-6305-4af5-a855-05cc3be60c55
      :target: https://github.com/nortikin/sverchok/assets/14288520/468bf917-6305-4af5-a855-05cc3be60c55

* **Check coincidence**. If enabled, then the node will check that the end
  points of curves being used do actually coincide (within threshold).
  If they do not, the node will give an error (become red), and the processing
  will stop. If this parameter is not enabled, then the node will do not check
  and will just assume that you've ensured the coincidence by yourself somehow
  (for example, you know that from the way you generated the curves). If the
  ends of curves do not coincide, the generated surface may be weird.
* **Max distance**. Maximum distance between end points of the curves, which is
  allowable to decide that they actually coincide. The default value is 0.001.
  This parameter is only available if **Check coincidence** parameter is
  enabled.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/ff3a1087-669e-4435-bcdb-f8ef603ee6d2
      :target: https://github.com/nortikin/sverchok/assets/14288520/ff3a1087-669e-4435-bcdb-f8ef603ee6d2

* **NURBS option**. This defines whether the node will generate a NURBS surface
  or a generic Surface object. The available options are:

   * **Generic**. Always create a generic Surface object.
   * **Always NURBS**. Create a NURBS surface. If input curves are not NURBS or
     NURBS-like, or if it is not possible to generate a NURBS surface for some
     another reason, the node will fail.
   * **NURBS if possible**. Create a NURBS surface. If input curves are not NURBS or
     NURBS-like, or if it is not possible to generate a NURBS surface for some
     another reason, the node will create a generic Surface object.

   The default option is **NURBS if possible**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/555a570e-eb2a-40e9-8eac-b625b28e840e
      :target: https://github.com/nortikin/sverchok/assets/14288520/555a570e-eb2a-40e9-8eac-b625b28e840e

Outputs
-------

This node has the following output:

* **Surface**. The generated surface.

Examples of usage
-----------------

Build four curves and generate a Coons patch from them:

.. image:: https://user-images.githubusercontent.com/284644/82479763-3f1c4c80-9aec-11ea-9a60-f01f0f9e1fa5.png
  :target: https://user-images.githubusercontent.com/284644/82479763-3f1c4c80-9aec-11ea-9a60-f01f0f9e1fa5.png

* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`

Similar example with "filleted polylines" as curves instead of cubic splines:

.. image:: https://user-images.githubusercontent.com/284644/82479766-404d7980-9aec-11ea-919b-50616556b5d6.png
  :target: https://user-images.githubusercontent.com/284644/82479766-404d7980-9aec-11ea-919b-50616556b5d6.png

* Curves->Curve Primitives-> :doc:`Fillet Polyline </nodes/curve/fillet_polyline>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`

One may use such surface to generate another topology:

.. image:: https://user-images.githubusercontent.com/284644/82479764-3fb4e300-9aec-11ea-8ddf-e4fce21f57a2.png
  :target: https://user-images.githubusercontent.com/284644/82479764-3fb4e300-9aec-11ea-8ddf-e4fce21f57a2.png

* Generator-> :doc:`Ring </nodes/generators_extended/ring_mk2>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`

It is possible to use the node together with "Split Curve" node to generate a surface from one closed curve:

.. image:: https://user-images.githubusercontent.com/284644/82479760-3deb1f80-9aec-11ea-8411-22ffd273259f.png
  :target: https://user-images.githubusercontent.com/284644/82479760-3deb1f80-9aec-11ea-8411-22ffd273259f.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Curves-> :doc:`Split Curve </nodes/curve/split_curve>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

It is possible to use only three boundary curves:

.. image:: https://user-images.githubusercontent.com/284644/210209607-113759b7-9992-4e5d-870d-6aa6dafe0c32.png
  :target: https://user-images.githubusercontent.com/284644/210209607-113759b7-9992-4e5d-870d-6aa6dafe0c32.png

* Curves-> :doc:`Bezier Spline Segment (Curve) </nodes/curve/bezier_spline>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw Surface </nodes/viz/viewer_draw_surface>`

If the third curve end does not coincide with the beginning of the first curve,
the node will close the cycle with a straight line segment:

.. image:: https://user-images.githubusercontent.com/284644/210209611-052c63b6-ef39-4c12-a047-d7d369f3469c.png
  :target: https://user-images.githubusercontent.com/284644/210209611-052c63b6-ef39-4c12-a047-d7d369f3469c.png

* Curves-> :doc:`Bezier Spline Segment (Curve) </nodes/curve/bezier_spline>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw Surface </nodes/viz/viewer_draw_surface>`
