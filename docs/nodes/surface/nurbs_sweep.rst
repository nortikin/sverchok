NURBS Sweep
===========

Dependencies
------------

This node can optionally use Geomdl_ library; it can also optionally use
FreeCAD_ libraries.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/
.. _FreeCAD: https://www.freecadweb.org/

Functionality
-------------

This node generates a NURBS Surface object by sweeping (extruding) one NURBS
curve (called "profile") along another NURBS curve (called "path").

Several profile curves can be also used; in this case the resulting surface
will be interpolaed between them.  
If several profile curves are used, the user can provide specific values of
path's curve T parameter, at which profile curves must be placed; otherwise,
the node will place them automatically evenly along T parameter of the path
curve.

It is supposed that initially the provided profile curve(s) are placed near
global origin. If profile curves passes through global origin, then the
resulting surface will go through the path curve.

The node works by placing several copies of profile curve along the path curve,
and then lofting (skinning) between them. If several profile curves are used,
then the node interpolates between them and places these interpolated curves
along the path curve.

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
* "Specified Y" algorithm selects rotation so that it satisfies two conditions:
  1) profile plane is perpendicular to curve's tangent vector, and 2) local Y
  axis of the profile curve points in general direction of "Normal" vector,
  provided by the user. This algorithm is supposed to give good results for
  planar or almost planar path curves. The resulting surface may have twists in places
  where original curve's tangent vector is parallel to offset operation plane's
  normal (i.e. tangent is perpendicular to offset operation plane).

This node is similar to "Extrude Curve along Curve" node; differences are:

* "NURBS Sweep" can work witn NURBS and NURBS-like curves only, while "Extrude
  Curve along Curve" works with arbitrary (e.g. formula-specified) Curve
  objects.
* "NURBS Sweep" node always generates a NURBS surface;  for such surface, some
  specific API methods can be applied; such surface can be saved in some file
  format, which understands only NURBS (at the moment, see "NURBS to JSON"
  node; later, nodes to save NURBS in some industry-used formats can appear).
* "NURBS Sweep" supports several profile curves.

At the moment, this node can effectively work with the following types of curves:

* NURBS curves
* Bezier curves
* Cubic splines
* Polylines
* Circular arcs
* Line segments

Some nodes, that output complex curves composed from simple curves (for
example, "Rounded rectangle"), have **NURBS output** parameter; when it is
checked, such nodes output NURBS curves, so "NURBS Loft" can work with them.

Inputs
------

This node has the following inputs:

* **Path**. The path curve, along which profile curves must be swept. This
  input is mandatory.
* **Profile**. Profile curve or curves. The node can work with one profile
  curve per path curve, or list of profile curves per path curve. This input is
  mandatory.
* **VSections**. Number of copies of profile curve (or interpolated curves, if
  several profile curves are used) the node will generate for lofting. This
  will be equal to number of control points of the resulting surface along it's
  V direction. Bigger values usually correspond to better precision of sweeping
  procedure; but too high numbers can cause weird results or be too slow. The
  default value is 10.
* **V**. Values of V parameter (i.e. path curve's T parameter), at which
  profile curves must be placed for lofting. This input is available and
  mandatory if **Explicit V Values** parameter is checked. The node expects
  number of values in this input equal to number of profile curves. For one
  profile curve, this input has no meaning.
* **Resolution**. Number of samples for **Zero-Twist** or **Track normal**
  rotation algorithm calculation. The more the number is, the more precise the
  calculation is, but the slower. The default value is 50. This input is only
  available when **Algorithm** parameter is set to **Zero-Twist** or **Track
  normal**.
* **Normal**. Orientation vector. This input is available only when
  **Algorithm** parameter is set to **Specified Y**. The default value is ``(0,
  1, 0)``.

Parameters
----------

This node has the following parameters:

* **Implementation**. This defines the implementation of NURBS mathematics to
  be used. The available options are:

  * **Geomdl**. Use Geomdl_ library. This option is available only when Geomdl
    package is installed.
  * **Sverchok**. Use built-in Sverchok implementation.
  * **FreCAD**. Use FreeCAD_ libraries. This option is available only when
    FreeCAD libraries are installed.
  
  In general, built-in implementation should be faster; but Geomdl
  implementation is better tested.  The default option is **Geomdl**, when it
  is available; otherwise, built-in implementation is used.

* **Algorithm**. Algorithm of calculating the orientation of profile curves
  with relation to path curve. The available options are:

  * **None**. Do not rotate the profile curve, just extrude it as it is. This mode is the default one.
  * **Frenet**. Rotate the profile curve according to Frenet frame of the extrusion curve.
  * **Zero-Twist**. Rotate the profile curve according to "zero-twist" frame of the extrusion curve.
  * **Householder**: calculate rotation by using Householder's reflection matrix
    (see Wikipedia_ article).                   
  * **Tracking**: use the same algorithm as in Blender's "TrackTo" kinematic
    constraint. This node currently always uses X as the Up axis.
  * **Rotation difference**: calculate rotation as rotation difference between two
    vectors.                                         
  * **Track normal**: try to maintain constant normal direction by tracking it along the curve.

* **Explicit V Values**. If checked, then the user has the ability to provide
  values of path curve's parameter values, at which the provided path curves
  must be placed; otherwise, the node will calculate these parameters
  automatically (evenly). This input has no meaning if there is only one
  profile curve.
* **U Knots**. This parameter is available in the N panel only. This defines
  how the node will modify input curves in order to make them use exactly the
  same knot vectors. Available options are:

  * **Unify**. Additional knots will be inserted for each curve in places where
    other curves have knots.
  * **Average**. Calculate knot vector by averaging knot vectors of the input
    curves. This can work only when input curves have the same number of
    control points.
  
  **Unify** option often generates a lot of additional control points for the
  resulting surface; it is more universal, and more precise in many cases.
  **Average** mode does not create additional control points, and so it works
  faster, and any following nodes working with the generated surface will work
  faster; but **Average** mode is less universal, and in many cases it gives
  less precise interpolations. The default value is **Unify**.

* **Metric**. This parameter is available in the N panel only. Distance type
  used for interpolation along V direction. The available values are:

   * Manhattan
   * Euclidian
   * Points (just number of points from the beginning)
   * Chebyshev
   * Centripetal (square root of Euclidian distance).

   The default option is Euclidian.

.. _Wikipedia: https://en.wikipedia.org/wiki/QR_decomposition#Using_Householder_reflections

Outputs
-------

This node has the following outputs:

* **Surface**. The generated NURBS surface.

Examples of usage
-----------------

One Profile curve:

.. image:: https://user-images.githubusercontent.com/284644/93505294-1a1dd600-f934-11ea-99cc-f9462affac3c.png

Two Profile curves:

.. image:: https://user-images.githubusercontent.com/284644/93505298-1b4f0300-f934-11ea-91c7-1bd7c7570789.png

Three Profile curves:

.. image:: https://user-images.githubusercontent.com/284644/93505300-1be79980-f934-11ea-9b0b-71d150312ca2.png

