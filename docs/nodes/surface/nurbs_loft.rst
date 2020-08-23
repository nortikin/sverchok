NURBS Loft
==========

Dependencies
------------

This node can optionally use Geomdl_ library.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/

Functionality
-------------

This node generates a NURBS Surface object from several NURBS or NURBS-like
Curves by applying so-called "skinning", or "lofting", operation. In a way,
"lofting" is interpolation of several curves to make a surface. So, this node
is somewhat similar to "Surface from Curves" node. Differences are:

* "NURBS Loft" can work only with NURBS and NURBS-like curves, while "Surface
  from Curves" works with arbitrary (e.g. formula-specified) curves.
* "NURBS Loft" node always generates a NURBS Surface; for such surface, some
  specific API methods can be applied; such surface can be saved in some file
  format, which understands only NURBS (at the moment, see "NURBS to JSON"
  node; later, nodes to save NURBS in some industry-used formats can appear).
* "NURBS Loft" usually works a lot faster comparing to "Surface from Curves".

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

This node also has a restriction concerning degrees of input curves. In order
for node to work, the input curves must:

* Either all have the same degree;
* Or, if some of curves have degree less than others, such smaller-degree
  curves must have number of control points equal to degree plus one.

Inputs
------

This node has the following inputs:

* **Curves**. Curves to make a loft from. This input can process data with
  nesting level up to 3 (list of lists of lists of curves), in order to use one
  value from **DegreeV** input per list of curves. This input is mandatory.
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
  
  In general, built-in implementation should be faster; but Geomdl
  implementation is better tested.  The default option is **Geomdl**, when it
  is available; otherwise, built-in implementation is used.

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
* **UnifiedCurves**. Curves that were actually used to construct the surface.
  These are the same curves as ones in the **Curves** input, but unified to
  have the same degree and knot vector.
* **VCurves**. Curves along V direction of the surface, which were used to
  calculate surface's control points during skinning process.

Example of usage
----------------

Generate several interpolating NURBS curves and draw a skinned surface through them:

.. image:: https://user-images.githubusercontent.com/284644/90965255-f5bf0d00-e4df-11ea-8498-dfbf3d26fd24.png

