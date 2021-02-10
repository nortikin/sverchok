NURBS Birail
============

Dependencies
------------

This node can optionally use Geomdl_ library; it can also optionally use
FreeCAD_ libraries.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/
.. _FreeCAD: https://www.freecadweb.org/

Functionality
-------------

This node generates a NURBS Surface object by sweeping one NURBS curve (called
"profile") along two other NURBS curves (called paths or rails), so that the
starting point of the profile goes along the first path, and the ending point
of the profile goes along the second path.

Several profile curves can be also used; in this case the resulting surface
will be interpolated between them.  
If several profile curves are used, the user can provide specific values of
path's curve T parameter, at which profile curves must be placed; otherwise,
the node will place them automatically evenly along T parameter of the path
curve.

It is supposed that initially th eprovided profile curve(s) lie in XOY plane.

The node works by placing several copies of profile curve along the path
curves, and then lofting (skinning) between them.  If several profile curves
are used, then the node interpolates between them and places these interpolated
curves along the path curve.  

This node can be compared with "NURBS Sweep" node. That node uses only one path
curve.

At the moment, this node can effectively work with the following types of curves:

* NURBS curves
* Bezier curves
* Cubic splines
* Polylines
* Circular arcs
* Line segments

Some nodes, that output complex curves composed from simple curves (for
example, "Rounded rectangle"), have **NURBS output** parameter; when it is
checked, such nodes output NURBS curves, so "NURBS Birail" can work with them.

Inputs
------

This node has the following inputs:

* **Path1**. The first path curve, along which profile curves must be swept.
  This input is mandatory.
* **Path2**. The second path curve, along which profile curves must be swept.
  This input is mandatory.
* **Profile**. Profile curve or curves. The node can work with one profile
  curve per path curve, or list of profile curves per path curve. This input is
  mandatory.
* **VSections**. Number of copies of profile curve (or interpolated curves, if
  several profile curves are used) the node will generate for lofting. This
  will be equal to number of control points of the resulting surface along it's
  V direction. Bigger values usually correspond to better precision of sweeping
  procedure; but too high numbers can cause weird results or be too slow. The
  default value is 10.
* **V1**, **V2**. Values of V parameter (i.e. path curve's T parameter), at which
  profile curves must be placed for lofting. This input is available and
  mandatory if **Explicit V Values** parameter is checked. The node expects
  number of values in this input equal to number of profile curves. For one
  profile curve, these inputs have no meaning. V1 input is for the first path,
  and V2 input is for the second path.
* **DegreeV**. Degree of NURBS curves used to interpolate in V direction. As
  most of Sverchok numeric inputs, this input can process data with nesting
  level up to 2 (list of lists of numbers). Degree of 1 will make a "linear
  loft", i.e. a surface composed from several ruled surfaces; higher degrees
  will create more smooth surfaces. The default value is 3. 

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

* **Scale all axes**. If not checked, profile curves will be scaled along one
  axis only, in order to fill the space between two paths. If checked, profile
  curves will be scaled along all axes uniformly. Checked by default.
* **Explicit V Values**. If checked, then the user has the ability to provide
  values of path curves parameter values, at which the provided path curves
  must be placed; otherwise, the node will calculate these parameters
  automatically (evenly). This parameter has no meaning if there is only one
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

Outputs
-------

This node has the following outputs:

* **Surface**. The generated NURBS surface.
* **AllProfiles**. Curves that were actually used to construct the surface.
  These are the curves provided in the **Profile** input, placed at their
  places along path curve and interpolated (if several profiles were used).
* **VCurves**. Curves along V direction of the surface, which were used to
  calculate surface's control points during skinning process.

Examples of usage
-----------------

1:

.. image:: https://user-images.githubusercontent.com/284644/98482006-30535e80-2220-11eb-9e4d-e1779e852abf.png

.. image:: https://user-images.githubusercontent.com/284644/98482008-31848b80-2220-11eb-876a-3ca5c3aae985.png

2:

.. image:: https://user-images.githubusercontent.com/284644/98482010-32b5b880-2220-11eb-9597-4ae339326748.png

.. image:: https://user-images.githubusercontent.com/284644/98482009-321d2200-2220-11eb-82a8-21ca366b573c.png

