Pipe (Curve)
============

Functionality
-------------

This node generates cylindrical "pipe" Surface along a given Curve; the result
is the same as if you extruded circular profile curve along your curve.

If you want more complex (not cylindrical) profile, or you want more control
over extrusion, you probably want to use "Extrude Curve Along Curve" node.

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
* **Resolution**. Number of samples for **Zero-Twist** or **Track normal**
  rotation algorithm calculation. The more the number is, the more precise the
  calculation is, but the slower. The default value is 50. This input is only
  available when **Algorithm** parameter is set to **Zero-Twist** or **Track
  normal**.

Parameters
----------

This node has the following parameters:

* **Algorithm**. Profile curve rotation calculation algorithm. The available options are:

  * **Frenet**. Rotate the profile curve according to Frenet frame of the extrusion curve.
  * **Zero-Twist**. Rotate the profile curve according to "zero-twist" frame of the extrusion curve.
  * **Householder**: calculate rotation by using Householder's reflection matrix
    (see Wikipedia_ article).                   
  * **Tracking**: use the same algorithm as in Blender's "TrackTo" kinematic
    constraint. This node currently always uses X as the Up axis.
  * **Rotation difference**: calculate rotation as rotation difference between two
    vectors.                                         
  * **Track normal**: try to maintain constant normal direction by tracking it along the curve.

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

