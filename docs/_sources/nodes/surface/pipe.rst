Pipe Surface Along Curve
========================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/88163a6e-5b0f-4e2b-a737-d9924eb7f222
  :target: https://github.com/nortikin/sverchok/assets/14288520/88163a6e-5b0f-4e2b-a737-d9924eb7f222

Functionality
-------------

This node generates cylindrical "pipe" Surface along a given Curve; the result
is the same as if you extruded circular profile curve along your curve.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/7e625f58-a153-45d6-a5e7-acfcbf4483c7
  :target: https://github.com/nortikin/sverchok/assets/14288520/7e625f58-a153-45d6-a5e7-acfcbf4483c7

If you want more complex (not cylindrical) profile, or you want more control
over extrusion, you probably want to use [:doc:`Surfaces-> Extrude Curve Along Curve </nodes/surface/extrude_curve>`] node. 

The Profile curve (circle) may optionally be rotated while extruding, to make result
look more naturally; though since the profile is always a circle, the choice of
algorithm is not so important for this node, usually.

Several algorithms to calculate rotation of profile curve are available. In
simplest cases, all of them will give very similar results. In more complex
cases, results will be very different. Different algorithms give best results
in different cases:

* "Frenet" or "Zero-Twist" algorithms give very good results in case when
  extrusion curve has non-zero curvature in all points. If the extrusion curve
  has zero curvature points, or, even worse, it has straight segments, these
  algorithms will either make "flipping" surface, or give an error.
* "Householder", "Tracking" and "Rotation difference" algorithms are
  "curve-agnostic", they work independently of curve by itself, depending only
  on tangent direction. They give "good enough" result (at least, without
  errors or sudden flips) for all extrusion curves, but may make twisted
  surfaces in some special cases.
* "Track normal" algorithm is supposed to give good results without twisting
  for all extrusion curves. It will give better results with higher values of
  "resolution" parameter, but that may be slow.

Surface domain: Along U direction - from 0 to ``2*pi``; along V direction - the
same as of "extrusion" curve.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to build pipe around (the extrusion curve). This input
  is mandatory.
* **Radius**. Pipe radius. The default value is 0.1.

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/45de54d3-db0b-41a0-8179-0e43a9743bb5
    :target: https://github.com/nortikin/sverchok/assets/14288520/45de54d3-db0b-41a0-8179-0e43a9743bb5

* **Resolution**. Number of samples for **Zero-Twist** or **Track normal**
  rotation algorithm calculation. The more the number is, the more precise the
  calculation is, but the slower. The default value is 50. This input is only
  available when **Algorithm** parameter is set to **Zero-Twist** or **Track
  normal**.

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/01d5f107-03a8-4fa6-af36-4ab3acc6637c
    :target: https://github.com/nortikin/sverchok/assets/14288520/f5dc1eb0-b9f3-48b9-9c01-8e6a87cb0079


Parameters
----------

This node has the following parameters:

* **Algorithm**. Profile curve rotation calculation algorithm. The available options are:

  * **Frenet**. Rotate the profile curve according to Frenet frame of the extrusion curve.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c23ded9a-f4dd-4e33-9449-0eb594af8526
      :target: https://github.com/nortikin/sverchok/assets/14288520/c23ded9a-f4dd-4e33-9449-0eb594af8526

  * **Zero-Twist**. Rotate the profile curve according to "zero-twist" frame of the extrusion curve.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/af300812-412b-410b-8f80-7d8460433fa7
      :target: https://github.com/nortikin/sverchok/assets/14288520/af300812-412b-410b-8f80-7d8460433fa7

  * **Householder**: calculate rotation by using Householder's reflection matrix
    (see Wikipedia_ article).

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/e6e754fb-ae3a-4c4a-920d-3bcfa83dcd70
      :target: https://github.com/nortikin/sverchok/assets/14288520/e6e754fb-ae3a-4c4a-920d-3bcfa83dcd70

  * **Tracking**: use the same algorithm as in Blender's "TrackTo" kinematic
    constraint. This node currently always uses X as the Up axis.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c8ee9171-193e-467b-aa7e-ff65ad3d5ed3
      :target: https://github.com/nortikin/sverchok/assets/14288520/c8ee9171-193e-467b-aa7e-ff65ad3d5ed3

  * **Rotation difference**: calculate rotation as rotation difference between two
    vectors.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c5a75e70-183e-4ef5-a185-592bcb6d10b0
      :target: https://github.com/nortikin/sverchok/assets/14288520/c5a75e70-183e-4ef5-a185-592bcb6d10b0

  * **Track normal**: try to maintain constant normal direction by tracking it along the curve.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/3d7d4e3f-a1a6-48f9-ad53-033824b02209
      :target: https://github.com/nortikin/sverchok/assets/14288520/3d7d4e3f-a1a6-48f9-ad53-033824b02209

  The default option is **Householder**.

.. _Wikipedia: https://en.wikipedia.org/wiki/QR_decomposition#Using_Householder_reflections

Outputs
-------

This node has the following output:

* **Surface**. The generated pipe surface.

Example of usage
----------------

Build a pipe from cubic curve:

.. image:: https://user-images.githubusercontent.com/284644/84814573-1e7fdd80-b02b-11ea-82d9-572288d7a770.png
  :target: https://user-images.githubusercontent.com/284644/84814573-1e7fdd80-b02b-11ea-82d9-572288d7a770.png

* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`


.. image:: https://github.com/nortikin/sverchok/assets/14288520/307f5bfb-0761-4afb-bc81-4ee73abb5cb6
  :target: https://github.com/nortikin/sverchok/assets/14288520/307f5bfb-0761-4afb-bc81-4ee73abb5cb6

* Generator->Generatots Extended-> :doc:`Hilbert 3D </nodes/generators_extended/hilbert3d>`
* Curves->Curve Primitives-> :doc:`Fillet Polyline </nodes/curve/fillet_polyline>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`