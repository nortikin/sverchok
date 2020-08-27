
NURBS: Curves and Surfaces
--------------------------

Among others, Sverchok supports a special kind of curves and surfaces, called
NURBS_ (Non-Uniform Rational B-Splines). NURBS objects are widely used in 3D
graphics, and, especially, in CAD software.

.. _NURBS: https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline

Blender itself has support of NURBS objects, but it is limited at the moment;
NURBS support in Sverchok is wider.

At the moment, Sverchok supports two implementations of NURBS mathematics:

* Geomdl_, a.k.a. NURBS-Python, library. It is relatively widely known and
  used, so we consider it as better tested. However, to use this
  implementation, you have to install Geomdl library into your Blender
  installation. Please refer to Dependencies_ wiki page for installation
  instructions.
* Built-in (native) implementation in Sverchok itself. In many cases, it is
  faster than Geomdl implementation, and it does not require any additional
  dependencies.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/
.. _Dependencies: https://github.com/nortikin/sverchok/wiki/Dependencies

Terminology
^^^^^^^^^^^

While widely used, for some reason, NURBS do not seem to have a "standard"
terminology: different software and different books use different terms for the
same things. Sverchok tries to not invent a 15th standard, and to follow the
terminology used in "The NURBS Book_". Here we are listing some common terms
for reference.

* **Control Point**: a point in 3D space, one of several points that define
  common shape of the curve or surface. In general, NURBS curve / surface does
  not go through it's control points, apart of some special cases. NURBS
  surfaces always have a rectangular grid of control points (m x n).
* **Weight**: a number, usually positive, which defines how strong a given
  control point "attracts" the curve or surface. Sverchok can work with
  negative weights usually, but there is a lot of software that can't, so
  usually you want to avoid use of negative weights.
* **Degree**: an integer number, from 1 to however you want, which is the
  degree of polynomials used in mathematical definition of NURBS curves. NURBS
  surfaces have two degrees: one along U direction, and another along V
  direction.
* **Non-rational B-Spline**, or simply **B-Spline**: a special kind of NURBS
  objects, that does not allow to specify weights; it is the same as a NURBS
  object with all weights set to 1.
* **Rational B-Spline**, or **NURBS**: a general kind of objects, that allows
  to specify different weights for different control points. Mathematically,
  such objects are defined as a relation of two polynomial expressions, hence
  the name "rational".
* **Knot vector**: a non-descending sequence of numbers, which define ranges of
  curve/surface parameters, to which different control points have some
  relation. It is hard to explain in a few words how exactly the knot vector
  affects the shape of curve of surface, so for details please refer to the
  literature. Each number in the knot vector is called **knot**. Knot vector of
  a NURBS curve with degree **p** and **n** control points always must contain
  **p + n + 1** knots. NURBS surfaces have two knot vectors: one for U
  parameter and one for V.
* **Knot multiplicity**. A number of times one knot is repeated in the knot
  vector. For example, if we have a knot vector ``0 1 2 2 2 3 4 5``, then we
  say that knot 2 has multiplicity of 3.
* **Uniform knot vector**: a knot vectors, values in which increase always by
  the same amount (uniformly). For example, ``0 1 2 3 4 5``. Sometimes this
  kind of knot vectors is called "periodic" (for reasons that we have no place
  to explain here). Uniform knot vectors are not very often used, because
  curves with such knot vectors do not pass through their first and last
  control points (in general).
* **Clamped knot vector**. A special kind of knot vector, which has
  multiplicity of it's first and last knots equal to **p +1**, where **p** is
  the degree of the curve (or surface, along one of directions). For example,
  if we are talking about a curve with degree equal to 2, then ``0 0 0 1 2 3 4
  5 5 5`` is a clamped knot vector. Curves with such knot vectors have a good
  property: they always pass through their first and last control points. This
  is a reason why clamped knot vectors are widely used.
* **Clamped Uniform knot vector**. Knot vector which is "almost uniform", but
  clamped; i.e. it has multiplicity of first and last knots equal to ``p+1``,
  but all other knots are ascending evenly. For example, ``0 0 1 2 3 4 4`` is a
  clamped uniform knot vector.
* **Non-Uniform knot vector**. Most general form of knot vectors. Knot vector,
  in which distance between neighbour knots is different in different places.
  For example, ``0 0 0.5 0.6 1.5 1.7 1.9 2 2 2`` is a non-uniform knot vector.

.. _Book: https://www.springer.com/gp/book/9783642973857

Workflow
^^^^^^^^

Some software has a "full NURBS workflow", which means that all curves /
surfaces it is operating with is always NURBS, and whatever complex things you
do with those objects you will always have NURBS again.
Sverchok does not have a goal to have "full NURBS workflow", at least at the
moment. Blender is, first of all, a mesh editing software, so, it is very
probable, that the most widely used workflow always will be to manipulate with
NURBS curves / objects for some time, together with other types of curves /
objects, but then convert them to mesh and apply some nodes that manipulate
with mesh, to receive a mesh in the end.

Some nodes have "NURBS output" parameter in their settings; when this parameter
is enabled, they output NURBS objects, otherwise a generic curve or surface is
generated.

There are some number of nodes, that can be called **NURBS-transparent**;
such nodes have a property: when they receive NURBS on the input, they will
always output NURBS. Examples of NURBS-transparent nodes are "Ruled Surface"
and "Surface of Revolution". Some nodes are NURBS-transparent only when you
enable some setting in them (see documentation of specific nodes). Number of
NURBS-transparent nodes will probably grow, but there is no guarantee that some
time all curve / surface processing nodes will become NURBS-transparent (and
there is no such goal at the moment).

"NURBS-transparent" nodes also automatically convert several special kinds of
curves into NURBS, when such curves are passed to inputs of such nodes. We call
types of curves, that can be automatically (and exactly, not approximately)
converted to NURBS, "NURBS-like". Examples of NURBS-like curves are:

* Bezier curves
* Cubic splines
* Polylines
* Circular arcs
* Line segments

Sverchok has "NURBS to JSON" and "JSON to NURBS" nodes, which allow to save
NURBS objects in JSON format and read NURBS from it; such JSON format can be
used with rw3dm_ utlity to convert it from / to `3dm` files.

.. _rw3dm: https://github.com/orbingol/rw3dm

Blender NURBS compatibility
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Blender's internal NURBS support is currently limited in two aspects:

* It's Python API for manipulating NURBS objects is very poor;
* It does not allow to specify an arbitrary knot vector for curve or surface;
  only two special kinds of knot vectors are supported: "clamped uniform knot
  vectors" and "uniform knot vectors".

So, Sverchok has limited features in interacting with Blender's native NURBS objects:

* **NURBS In** object can bring arbitrary Blender's NURBS curves or surfaces
  from scene to Sverchok space;
* **NURBS Curve Out** and **NURBS Surface Out** nodes allow to generate
  Blender's NURBS objects in scene, but without possibility to specify
  arbitrary knot vectors.

