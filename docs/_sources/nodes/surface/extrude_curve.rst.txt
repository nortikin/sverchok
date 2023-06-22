Extrude Curve Along Curve
=========================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/ed067f3d-ab41-472f-9091-55ff974151ae
  :target: https://github.com/nortikin/sverchok/assets/14288520/ed067f3d-ab41-472f-9091-55ff974151ae

Functionality
-------------

This node generates a Surface object by extruding one Curve (called "profile")
along another Curve (called "Extrusion").

.. image:: https://github.com/nortikin/sverchok/assets/14288520/cfe0ca7a-6f3b-4ea1-9600-64eb1e4e1ae2
  :target: https://github.com/nortikin/sverchok/assets/14288520/cfe0ca7a-6f3b-4ea1-9600-64eb1e4e1ae2

In case your Profile curve is just a circle with center at global origin, you
may wish to use simpler "Pipe (Surface)" node. **Surfaces**-> :doc:`Pipe Surface Along Curve </nodes/surface/pipe>`

It is supposed that the profile curve is positioned so that it's "logical
center" (i.e., the point, which is to be moved along the extrusion curve) is
located at the global origin `(0, 0, 0)`.

The Profile curve may optionally be rotated while extruding, to make result
look more naturally.

Several algorithms to calculate rotation of profile curve are available. In
simplest cases, all of them will give very similar results. In more complex
cases, results will be very different. Different algorithms give best results
in different cases:

* "Frenet" or "Zero-Twist" algorithms give very good results in case when
  extrusion curve has non-zero curvature in all points. If the extrusion curve
  has zero curvature points, or, even worse, it has straight segments, these
  algorithms will either make "flipping" surface, or give an error.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/d8f864f9-bbf2-45c7-8aab-093fca67a319
      :target: https://github.com/nortikin/sverchok/assets/14288520/d8f864f9-bbf2-45c7-8aab-093fca67a319

* "Householder", "Tracking" and "Rotation difference" algorithms are
  "curve-agnostic", they work independently of curve by itself, depending only
  on tangent direction. They give "good enough" result (at least, without
  errors or sudden flips) for all extrusion curves, but may make twisted
  surfaces in some special cases.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/bd70222a-02a6-4313-a56c-261a16246091
      :target: https://github.com/nortikin/sverchok/assets/14288520/bd70222a-02a6-4313-a56c-261a16246091

* "Track normal" algorithm is supposed to give good results without twisting
  for all extrusion curves. It will give better results with higher values of
  "resolution" parameter, but that may be slow.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/402eec26-871c-4ad1-8242-4fc7001c04ea
      :target: https://github.com/nortikin/sverchok/assets/14288520/402eec26-871c-4ad1-8242-4fc7001c04ea

Surface domain: Along U direction - the same as of "profile" curve; along V
direction - the same as of "extrusion" curve.

Inputs
------

This node has the following inputs:

* **Profile**. The profile curve (one which is to be extruded). This input is mandatory.
* **Extrusion**. The extrusion curve (the curve along which the profile is to
  be extruded). This input is mandatory.
* **Resolution**. Number of samples for **Zero-Twist** or **Track normal**
  rotation algorithm calculation. The more the number is, the more precise the
  calculation is, but the slower. The default value is 50. This input is only
  available when **Algorithm** parameter is set to **Zero-Twist** or **Track
  normal**.

Parameters
----------

This node has the following parameters:

* **Algorithm**. Profile curve rotation calculation algorithm. The available options are:

  * **None**. Do not rotate the profile curve, just extrude it as it is. This mode is the default one.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/1763bade-f569-4727-9c9c-033757411ada
      :target: https://github.com/nortikin/sverchok/assets/14288520/1763bade-f569-4727-9c9c-033757411ada

  * **Frenet**. Rotate the profile curve according to Frenet frame of the extrusion curve.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/81a0de4a-168a-49d5-a32a-5ca4e45baeee
      :target: https://github.com/nortikin/sverchok/assets/14288520/81a0de4a-168a-49d5-a32a-5ca4e45baeee

  * **Zero-Twist**. Rotate the profile curve according to "zero-twist" frame of the extrusion curve.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/3447e45a-f174-45cb-a540-b7d1875ffb19
      :target: https://github.com/nortikin/sverchok/assets/14288520/3447e45a-f174-45cb-a540-b7d1875ffb19

  * **Householder**: calculate rotation by using Householder's reflection matrix
    (see Wikipedia_ article).      

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/02784b8f-0f16-4d62-8ecd-9f0c496c4f91
      :target: https://github.com/nortikin/sverchok/assets/14288520/02784b8f-0f16-4d62-8ecd-9f0c496c4f91

  * **Tracking**: use the same algorithm as in Blender's "TrackTo" kinematic
    constraint. This node currently always uses X as the Up axis.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/91f7faa4-7219-4beb-8387-80af68f0360e
      :target: https://github.com/nortikin/sverchok/assets/14288520/91f7faa4-7219-4beb-8387-80af68f0360e

  * **Rotation difference**: calculate rotation as rotation difference between two
    vectors.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/e2fcd8f4-775a-43b3-9372-ea363a203bd7
      :target: https://github.com/nortikin/sverchok/assets/14288520/e2fcd8f4-775a-43b3-9372-ea363a203bd7

  * **Track normal**: try to maintain constant normal direction by tracking it along the curve.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/b651eae4-23e8-41cb-a1c2-5c8f0dc77595
      :target: https://github.com/nortikin/sverchok/assets/14288520/b651eae4-23e8-41cb-a1c2-5c8f0dc77595

  * **Specified plane**: Use plane defined by normal vector in Normal input; i.e., offset in direction
    perpendicular to Normal input

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/7c651b14-65f7-4549-859b-0bb168122271
      :target: https://github.com/nortikin/sverchok/assets/14288520/7c651b14-65f7-4549-859b-0bb168122271

* **Origin**. This parameter defines the position of the resulting surface with
  relation to the positions of the profile curve and the extrusion curve. It is
  useful when the beginning of the extrusion curve does not coincide with
  global origin `(0, 0, 0)`. The available options are:

   * **Global origin**. The beginning of the surface will be placed at global origin.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/7b616060-5c58-4070-b124-9e78697d0769
      :target: https://github.com/nortikin/sverchok/assets/14288520/7b616060-5c58-4070-b124-9e78697d0769

   * **Extrusion origin**. The beginning of the surface will be placed at the beginning of the extrusion curve.
   
    .. image:: https://github.com/nortikin/sverchok/assets/14288520/baef4ac2-7e3e-4d95-80e8-71257556238f
      :target: https://github.com/nortikin/sverchok/assets/14288520/baef4ac2-7e3e-4d95-80e8-71257556238f

  The default option is **Extrusion origin**.

.. _Wikipedia: https://en.wikipedia.org/wiki/QR_decomposition#Using_Householder_reflections

Outputs
-------

This node has the following output:

* **Surface**. The generated surface.

Examples of usage
-----------------

"None" algorithm works fine in many simple cases:

.. image:: https://user-images.githubusercontent.com/284644/79357796-eb04d200-7f59-11ea-8ef1-cb35ebb0083e.png
  :target: https://user-images.githubusercontent.com/284644/79357796-eb04d200-7f59-11ea-8ef1-cb35ebb0083e.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Curves->Curve Primitives-> :doc:`Polyline </nodes/curve/polyline>`
* Curves->Curve Primitives-> :doc:`Fillet Polyline </nodes/curve/fillet_polyline>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

It becomes not so good if the extrusion curve has some rotations:

.. image:: https://user-images.githubusercontent.com/284644/79357777-e5a78780-7f59-11ea-8f08-ba309965b67c.png
  :target: https://user-images.githubusercontent.com/284644/79357777-e5a78780-7f59-11ea-8f08-ba309965b67c.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Curves->Curve Primitives-> :doc:`Polyline </nodes/curve/polyline>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Similar case with "Frenet" algorithm:

.. image:: https://user-images.githubusercontent.com/284644/79357785-e809e180-7f59-11ea-976a-a2bc32388ee0.png
  :target: https://user-images.githubusercontent.com/284644/79357785-e809e180-7f59-11ea-976a-a2bc32388ee0.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Curves->Curve Primitives-> :doc:`Polyline </nodes/curve/polyline>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

The same with "Zero-Twist" algorithm:

.. image:: https://user-images.githubusercontent.com/284644/79357791-e93b0e80-7f59-11ea-9f8f-e74e1eead4cb.png
  :target: https://user-images.githubusercontent.com/284644/79357791-e93b0e80-7f59-11ea-9f8f-e74e1eead4cb.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Curves->Curve Primitives-> :doc:`Polyline </nodes/curve/polyline>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
