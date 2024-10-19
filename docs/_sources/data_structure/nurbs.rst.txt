
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
* FreeCAD_ libraries. FreeCAD uses OpenCASCADE kernel, which is implemented in
  C++, so it is faster than Geomdl implementation; it is also considered to be
  more widely tested compared to Sverchok built-in implementation. However, it
  is in general slower comparing to built-in implementation, when you want to
  evaluate a lot of points on one curve or surface. Please refer to
  Dependencies_ wiki page for installation instructions.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/
.. _FreeCAD: https://www.freecadweb.org/
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
* **Control Polygon** (for a curve): a polygon composed from control points of
  a curve, connected with edges.
* **Control Net** (for a surface): a grid-like mesh, composed from control
  points of a surface, connected with edges.
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
  exactly **p + n + 1** knots. NURBS surfaces have two knot vectors: one for U
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
  For example, ``0 0 0.5 0.6 1.5 1.7 1.9 2 2 2`` is a non-uniform (and clamped)
  knot vector.
* **Node values**, **Node points**. Also known as Greville abscissaes and
  Greville points, average knot values, or simply edit points. The values of
  NURBS curve's T parameter, defined as: ``t[i] = sum(u[i+j] for j from 1 to p)
  / p``, where ``u`` is curve's knotvector, and ``p`` is curve's degree.  NURBS
  curve *node points* (or Greville points) are points at the curve at parameter
  values equal to node values.  The number of curve's nodes is equal to the
  number of curve's control points.  Node points of the curve are positioned on
  the curve near corresponding control points. So in many NURBS algorithms,
  node points are used to define the shape of NURBS curve, instead of control
  points.

.. _Book: https://www.springer.com/gp/book/9783642973857

Bezier Curves
^^^^^^^^^^^^^

One of most used types of curves in 2D and 3D graphics is Bezier curves.
Technically, Bezier curves constitute a very simple special case of NURBS
curves. Bezier curve of degree **p** has exactly **p+1** control points.
Technically, there exist "rational Bezier curves", i.e. Bezier curves with
weights; but in most software  (including Blender), non-rational Bezier curves
(without weights) are used.
Usually Bezier curves of 2nd and 3rd degree are used, so they have
correspondingly 3 or 4 control points. As such, Bezier curves can not give much
flexiblity of shape. For example, quadratic Bezier curve always has shape of an
arc. Cubic Bezier curve can be "S-shaped" or "C-shaped". To make more complex
forms, more control points (and, thus, higher degree) would be needed.
But in most 2D and 3D graphics software, there is widely spread misuse of
terminology. In software, one usually composes complex curves of several
sequential Bezier segments of 2nd or 3rd degree. Technically, such curve is not
Bezier curve, it is a NURBS curve of general form. However, since it is
composed of Bezier curves, in software such curves are usually themselves
called Bezier curves. In such case, initial Bezier curves which composed the
complex curve, are called "Bezier segments" or "Bezier splines". Such
terminology is used in Inkscape and in Blender, for example.

NURBS-like curves
^^^^^^^^^^^^^^^^^

Some kinds of curves are not NURBS curves "by construction", but can be
represented (exactly, not approximately) as NURBS curves. We call such curves
"NURBS-like curves". Examples of NURBS-like curves are:

* Straight line segments
* Polylines
* Bezier curves (and also curves composed of several Bezier segments, as it was
  explained earlier)
* Cubic splines
* Catmull-Rom splines
* Circles and circular arcs; ellipses and elliptic arcs. This case is a bit
  special. One can build a NURBS curve which has an exact shape of a circle.
  However, curve parametrization would differ from standard ("natural")
  parametrization of a circle. The same goes for circluar arcs, ellipses and
  elliptic arcs.

Workflow
^^^^^^^^

Some software products have a "full NURBS workflow", which means that all curves /
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

"NURBS-transparent" nodes also automatically convert "NURBS-like" curves into
NURBS, when such curves are passed to inputs of such nodes.

Sverchok has "NURBS to JSON" and "JSON to NURBS" nodes, which allow to save
NURBS objects in JSON format and read NURBS from it; such JSON format can be
used with rw3dm_ utility to convert it from / to `3dm` files. Later there can
appear nodes that will export NURBS objects to other widely-used formats.

So, with some restrictions, it is possible to prepare complex scenes built from
NURBS objects only, to export them to other CAD software for further processing
or manufacturing. This is, however, not a primary workflow at the moment.

.. _rw3dm: https://github.com/orbingol/rw3dm

Blender NURBS compatibility
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Blender's internal NURBS support is currently limited in two aspects:

* It's Python API for manipulating NURBS objects is very poor;
* It does not allow to specify an arbitrary knot vector for curve or surface;
  only two special kinds of knot vectors are supported: "clamped uniform knot
  vectors" and "uniform knot vectors".

So, Sverchok has limited features in interacting with Blender's native NURBS objects:

* **NURBS Input** node can bring arbitrary Blender's NURBS curves or surfaces
  from scene to Sverchok space;
* **NURBS Curve Out** and **NURBS Surface Out** nodes allow to generate
  Blender's NURBS objects in scene, but without possibility to specify
  arbitrary knot vectors.

