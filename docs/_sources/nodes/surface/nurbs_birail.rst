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

By default it is supposed that initially the provided profile curve(s) lie in
XOY plane. However, there is an option to instruct the node to try to figure
out correct rotation of profile curve(s). Note that this option may result in
precision loss in some cases. Or, in other cases, it can guess desired profile
rotation incorrectly. In such cases, you will have to place your profile curves
in XOY plane and disable "Auto rotate" flag.

The node works by placing several copies of profile curve along the path
curves. If several profile curves are used, then the node interpolates between
them and places these interpolated curves along the path curve. Then one of
two algorithms can be used:

* **Lofting** (legacy). A loft surface is generated from profile curves placed
  along path curves.
* **Gordon**. Gordon surface is generated from path curves and profile curves.
  See documentation of "Surface from NURBS curves net" node for more information.

Loft algorithm works faster with the same number of profile curve copies
(**VSections** parameter). But, in order for resulting surface to touch path
curves precisely enough, you usually will have to use high enough value of
VSections parameter. Gordon algorithm produces the surface which always touches
path curves precisely, even with small number of V sections. But Gordon
algorithm is slower, and it produces surfaces with more control points. Also,
Gordon algorithm does not support (yet) rational curves. One can either use
Loft algorithm for such curves, or pass curves through "Curve to NURBS" node to
make them non-rational.

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
  mandatory if **Profile V values** parameter is set to **Explicit**. The node
  expects number of values in this input equal to number of profile curves. The
  values fed in V1 and V2 must be in an ascending order, e.g. ``(0.0, 0.333,
  0.667, 1.0)``. For one profile curve, these inputs have no meaning. V1 input
  is for the first path, and V2 input is for the second path.
* **DegreeV**. Degree of NURBS curves used to interpolate in V direction. As
  most of Sverchok numeric inputs, this input can process data with nesting
  level up to 2 (list of lists of numbers). Degree of 1 will make a "linear
  loft", i.e. a surface composed from several ruled surfaces; higher degrees
  will create more smooth surfaces. The default value is 3. 
* **Length Resolution**. This input is available only when **Profile V values**
  parameter is set to **Path length uniform**. Defines the resolution to be
  used for calculation of path curves length. The default value is 50.
* **Normal**. This input is available only when **Profile Rotation** parameter
  is set to **Custom**. Vector which controls orientation of copies of profile
  curves along path curves. The node will try to rotate profile curves so that
  they would lie in the same plane with specified vector. This is not exactly
  possible in many situations, but at least approximately the profiles will be
  rotated this way. The default value is ``(0, 0, 1)`` (Z axis).

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

* **Algorithm**. The available algorithms are **Loft** and **Gordon Surface**.
  See description above. The default one is **Gordon Surface**.
* **Scale all axes**. If not checked, profile curves will be scaled along one
  axis only, in order to fill the space between two paths. If checked, profile
  curves will be scaled along all axes uniformly. Checked by default.
* **Auto rotate profiles**. If not checked, the node will assume that all
  profile curves lie in the XOY plane. If checked, the node will work with
  arbitrarily rotated profile curves. Enabled option requires more
  computations, and so, may make the node slower and less precise. Unchecked by
  default.
* **Profile Rotation**. This defines how profile curves will be placed along
  the path curves. The available options are:
  
   * **Path Normal Average**. The node will try to place profile curves so that
     they will lie in normal planes of both path curves. Since normal planes of
     two path curves can differ, the node will calculate average normal plane.
   * **Path 1 Normal**. The node will place profile curves so that they lie in
     normal plane of the first path curve.
   * **Path 2 Normal**. The node will place profile curves so that they lie in
     normal plane of the second path curve.
   * **By profile**. The node will try to place profile curves so that they be
     parallel to initial location of the path curve. This is not always
     possible, but the node will try to keep it as parallel as possible.
   * **Custom**. The node will try to place profile curves so that they be
     parallel to the vector specified in the **Normal** input. This is not
     always possible, but the node will try to keep it as parallel as possible.

   The default option is **Path Normal Average**.

* **Profile V values**. Controls how copies of profile curve(s) are distributed
  along path curves. The following options are available:

  * **Path parameter uniform**. Distribute profile curves uniformly according
    to path curve parametrization. This is the fastest and default option.
  * **Path length uniform**. Distribute profile curves uniformly according to
    path curve length segments (natural parametrization). Can generate more
    "natural" forms if path curves parametrization is too far from natural
    parametrization. Note that if Gordon algorithm is used, then with this mode
    you will get a surface with more control points. Also, if parametrization
    of two path curves differs from each other too much, then with Gordon
    algorithm the resulting surface can be not very smooth in some places. If
    you need profile curves distributed uniformly along path curves, but this
    option together with Gordon algorithm give you too strong artifacts, you
    may wish to use "Curve to NURBS" node on both path curves before passing
    them to this node.
  * **Explicit**. In this mode, the user has the ability to provide values of
    path curves parameter values, at which the provided path curves must be
    placed. Caveats about Gordon algorithm (see previous option) apply to
    this option as well. This option has no meaning if there is only one
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
  
* **Knotvector accuracy**. This parameter is available in the N panel only.
  Accuracy (number of exact digits after decimal points) to be used for
  knotvector unification algorithm. The default value is 6. Usually you do not
  have to modify this parameter; but, if your curves have a lot of control
  points (like, hundreds of them), or if knot values in curves knotvectors are
  very near one another, you may wish to reduce accuracy in order to reduce the
  number of control points in the resulting surface (the result will be less
  precise, but will work faster).

* **Metric**. This parameter is available in the N panel only. Distance type
  used for interpolation along V direction. The available values are:

   * Manhattan
   * Euclidean
   * Points (just number of points from the beginning)
   * Chebyshev
   * Centripetal (square root of Euclidean distance).

   The default option is Euclidean.

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

Create a circular arc (path 1) and S-shaped curve (path 2); use random profile curve in YOZ plane. Profile rotation = Path Normal Average (default one):

.. image:: https://user-images.githubusercontent.com/284644/122664399-9347a380-d1ba-11eb-98fc-6ce8c10ad6fe.png

Same with Profile rotation = Path 1 Normal (i.e. profiles are perpendicular to the lower curve, circular arc):

.. image:: https://user-images.githubusercontent.com/284644/122664398-92af0d00-d1ba-11eb-921f-9cf0289b5356.png

Same with Profile rotation = Path 2 Normal (i.e. profiles are perpendicular to the upper, S-shaped curve):

.. image:: https://user-images.githubusercontent.com/284644/122664396-92af0d00-d1ba-11eb-8a40-95fde688941e.png

Same with Profile rotation = By profile, i.e. try to keep profile curves parallel to the original profile:

.. image:: https://user-images.githubusercontent.com/284644/122664393-917de000-d1ba-11eb-880a-44b53bf159bd.png

Another example; initial curves (with red points you can see how non-uniform is parametrization of path curves):

.. image:: https://github.com/user-attachments/assets/2ec7d3ff-3293-4e8c-989e-54ccc7ae0144
  :target: https://github.com/user-attachments/assets/2ec7d3ff-3293-4e8c-989e-54ccc7ae0144

Loft algorithm result (with default "Path parameter uniform" distribution of
profiles). Here we use low number of VSections (just 4 of them) to show that in
such a case with Loft algorithm the surface may not follow path curves exactly:

.. image:: https://github.com/user-attachments/assets/e9e7f655-305d-4f74-a130-4281ff627abd
  :target: https://github.com/user-attachments/assets/e9e7f655-305d-4f74-a130-4281ff627abd

Gordon algorithm result (with the same "path parameter uniform" distribution of
profiles). The same numer of VSections is used. Now the surface follows paths
exactly, but you can see that iso-curves of the resulting surface are going
"diagonally" - that's because path curves parametrization is non-uniform (and
parametrization of two path curves is very different):

.. image:: https://github.com/user-attachments/assets/79f32682-8704-41fc-944f-9e114f162bdf
  :target: https://github.com/user-attachments/assets/79f32682-8704-41fc-944f-9e114f162bdf


Gordon algorithm with "path length uniform" distribution of profiles. Here
iso-curves go much more straight:

.. image:: https://github.com/user-attachments/assets/81d2b638-9946-4d1f-802f-cd9795b2be37
  :target: https://github.com/user-attachments/assets/81d2b638-9946-4d1f-802f-cd9795b2be37

