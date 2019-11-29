Bevel a Curve
=============

Functionality
-------------

This node provides functionality similar to Blender's standard "bevel curve"
feature_. More precisely, it extrudes one flat curve (called "bevel object")
along another curve (path). Scale of "bevel object" may vary along the curve,
as it is controlled by third curve (called "taper object").

.. _feature: https://docs.blender.org/manual/en/latest/modeling/curves/properties/geometry.html

The curve to extrude along, as well as taper curve, may be defined as a cubic
spline or as a linear spline.

It is in general not a trivial task to rotate a 3D object along a vector,
because there are always 2 other axes of object and it is not clear where
should they be directed to. So, this node supports 3 different algorithms of
object rotation calculation. In many simple cases, all these algorithms will
give exactly the same result. But in more complex setups, or in some corner
cases, results can be very different. So, just try all algorithms and see which
one fits you better.

**Note 1**: "Bevel object" can be open or closed; it may even consist of
several separate fragments. But it is supposed to be **flat** object, laying in
one of coordinate planes (XY, YZ or XZ). This plane defines the so-called
"orientation axis" - a coordinate axis, which is perpendicular to "bevel
object"; during extrusion, bevel object will be moved along orientation axis.

**Note 2**: "Taper object" is supposed to be an open curve, elongated along one of
coordinate axes (X, Y or Z). That must be the orientation axis, i.e. the axis
perpendicular to the plane of bevel object.

In the most common case, "bevel object" will lay in XY plane, so that orientation axis will be Z.

Inputs
------

This node has the following inputs:

* **Curve**. List of vertices, which define the curve, along which the bevel
  will be made. Order of vertices in this input must be the same as the order
  of vertices on the curve being defined. If you are using an "Object In" node
  to provide this curve, you may want to use "Vector Sort" node in
  "connections" mode to sort vertices properly. This input is mandatory.
* **BevelVerts**. List of vertices, which define the "bevel object". This input is mandatory.
* **BevelEdges**. List of edges of "bevel object". You may not connect this
  input if you connected the **BevelFaces** input: in such a case, edges will be
  derived automatically from faces.
* **BevelFaces**. List of faces of "bevel object". This input is optional, but may be very
  important for some bevel objects if you use **Cap Start** or **Cap End** options.
* **TaperVerts**. List of vertices, which define the taper curve. This input is
  optional. If it is not connected, then scale of the bevel object will be
  constant.
* **Twist**. Data that define rotation of the bevel object around the
  orientation axis during extrusion. The following types of data are supported:

  - List of `(t, twist)` pairs, where `t` is a number between 0 and 1 and
    `twist` is an angle (in radians, growing counterclockwise). Each of these
    pairs defines what angle should bevel object rotated by at point `t`; `t =
    0` means the beginning of the curve and `t = 1` denotes the end of the
    curve. For example, if `[(0, 0), (1, 6.28)]` is passed into this input,
    this will mean that at the beginning of the curve the bevel object should
    not be rotated, and at the end of the curve the bevel object should be
    rotated by one full turn (`2*pi`).
  - List of numbers. In this case, numbers passed are interpreted as twist
    angles; `t` values are supposed to be evenly growing from 0 to 1. For
    example, you may pass `[0, 3.14, 0]` into this input, and it will mean
    exactly the same as `[(0, 0), (0.5, 3.14), (1.0, 0)]`.

  Between points defined in this input, twist angles can be interpolated either
  by linear or by cubic spline.
  If this input is not connected, it will mean that no additional twist is
  added.
  Note that twist is added to rotation defined by rotation calculation
  algorithm (see below).

* **Steps**. Number of subdivisions (steps) in which the curve must be
  evaluated. Default value is 10.

Parameters
----------

This node has the following parameters:

- **Orientation**. The axis of "bevel object", which should be oriented along
  the path. Default value is Z (which means that bevel object should lay in XY plane).
- **Algorithm**. Rotation calculation algorithm. Available values are:

  * Householder: calculate rotation by using Householder's reflection matrix
    (see Wikipedia_ article).                   
  * Tracking: use the same algorithm as in Blender's "TrackTo" kinematic
    constraint. This algorithm gives you a bit more flexibility comparing to
    other, by allowing to select the Up axis.                                                         
  * Rotation difference: calculate rotation as rotation difference between two
    vectors.                                         

  Default value is Householder.

- **Up axis**.  Axis of donor object that should point up in result. This
  parameter is available only when Tracking algorithm is selected.  Value of
  this parameter must differ from **Orientation** parameter, otherwise you will
  get an error. Default value is X.
- **Curve Mode**. Path interpolation mode. Available values are Linear and Cubic.
  Default value is Cubic.
- **Taper Mode**. Taper curve interpolation mode. Available values are Linear
  and Cubic. Default value is Cubic.
- **Twist Mode**. Twist angles interpolation mode. Available values are Linear
  and Cubic. Default value is Linear.
- **Cyclic**. Indicate whether the path is cyclic. Default value is false.
- **Separate Scale**. Whether the scale of bevel object defined by taper object
  should be the same along both axes, or it may differ:

  * If checked: scale of the bevel object along X axis is defined by X
    coordinates of the vertices of taper curve, and scale of the bevel object
    along Y axis is defined by Y coordinates of taper curve vertices.
  * If not checked: scale of the bevel object along X and Y axes will be always
    the same, defined as `sqrt(X*X + Y*Y)`, where X and Y are coordinates of
    taper curve vertex.
  
  (here it is supposed that orientation axis is Z, for other orientation axes
  logic is similar).

  This parameter has no meaning if **TaperVerts** input is not connected.

  Unchecked by default.

- **Cap Start**. Whether to create a cap faces at the beginning of curve.
  Unchecked by default.
- **Cap End**. Whether to create a cap faces at the end of curve.  Unchecked by
  default.
- **Flip Curve**. This parameter is available only in the N panel. If checked,
  then direction of the curve is inverted comparing to the order of path vertices
  provided. Unchecked by default.
- **Flip Taper**.  This parameter is available only in the N panel. If checked,
  then direction of the taper curve is inverted comparing to the order of path
  vertices provided. Unchecked by default.
- **Flip Twist**.  This parameter is available only in the N panel. If checked,
  then direction of the twist data is inverted comparing to the order of path
  vertices provided. Unchecked by default.
- **Metric**. The metric to use to compute argument values of the spline, which
  correspond to path vertices provided. Available values are: Euclidean,
  Manhattan, Chebyshev, Points. Default value is Euclidean. The default metric
  usually gives good results. If you do not like results, try other options.
  This parameter is available only in the N panel. 
- **Taper Metric**. Defines the metric to use to calculate the spline for taper
  object. Available values are:
  * **Same as Curve** - use the same metric as for main curve. In many cases,
    this algorithm may be very imprecise.
  * **Orientation Axis** - use coordinates of taper object's vertices along the
    orientation axis. This usually gives more precise result. This mode
    assumes, that the taper object is oriented along that orientation axis: for
    example, if orientation axis is Z, then each following vertex of taper
    object must have Z coordinate bigger than previous vertex. This value is
    the default one.

- **Tangent precision**. Step to be used to calculate tangents of the spline.
  Lesser values correspond to better precision. In most cases, you will not
  have to change the default value. This parameter is available only in the N panel. 

.. _Wikipedia: https://en.wikipedia.org/wiki/QR_decomposition#Using_Householder_reflections

Outputs
-------

This node has the following outputs:

* **Vertices**. Output object vertices.
* **Edges**
* **Faces**

Examples of usage
-----------------

Simplest example:

.. image:: https://user-images.githubusercontent.com/284644/59158004-62add900-8acd-11e9-95be-b99908457243.png

Example with cyclic curve:

.. image:: https://user-images.githubusercontent.com/284644/59157904-73118400-8acc-11e9-8d1d-beef6870d29c.png

Example of taper curve usage:

.. image:: https://user-images.githubusercontent.com/284644/59160367-83d2f180-8aee-11e9-8d3b-8ec704e9ff24.png

Example of **Separate Scale** option usage:

.. image:: https://user-images.githubusercontent.com/284644/59159604-c0e6b600-8ae5-11e9-8fea-1ede6da5caf0.png

The same setup with **Separate Scale** disabled:

.. image:: https://user-images.githubusercontent.com/284644/59159605-c17f4c80-8ae5-11e9-8290-a3487e1d5277.png

Example of the **Twist** input use:

.. image:: https://user-images.githubusercontent.com/284644/65392001-50f4f680-dd89-11e9-99ce-e3b1ab8f0c12.png

You can also find some more examples `in the development thread <https://github.com/nortikin/sverchok/pull/2442>`_.

