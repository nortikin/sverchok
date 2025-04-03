Refine NURBS Curve
==================

Functionality
-------------

This node performs "refinement" procedure on a NURBS curve, i.e. inserts a
number of knots in order to make it easier to manipulate with curve's shape.
Each knot can be inserted once or multiple times. Knots are distributed
according to one of algorithms, in order to make knots distribution more even.

After some modifications to refined curve shape were done, unneeded knots can be
removed by use of "Remove excessive knots (Curve)" node.

Inputs
------

This node has the following inputs:

* **Curve**. The NURBS Curve object to be refined. This input is mandatory.
* **NewKnots**. The number of knots to be inserted. The default value is 10.
* **Resolution**. Resolution of the algorithm which is used to calculate curve
  arc lengths (see the documentation of "Curve Length" node, for example).
  Larger values correspond to better precision, but worse performance. The
  default value is 50. This input is only available when the **Distribution**
  parameter is set to **Distribute Length** or **Bisect Length**.
* **TMin**, **TMax**. Minimum and maximum values of curve's T parameters,
  between which the new knots are to be inserted. These inputs are available
  only when the **Specify Segment** parameter is checked. The default values
  are 0.0 and 1.0, correspondingly.

Parameters
----------

This node has the following parameters:

* **Distribution**. The algorithm used to distribute curve's knots evenly. The available options are:

  * **Even T**. New knots are distributed evenly in curve's T space, not taking
    into account the fact that previously existing curve knots can lie near to
    newly inserted knots. This option is the default.
  * **Distribute T**. New knots are inserted into each segment between existing
    curve knots, distributed evenly (in curve's parameter space) inside each
    segment. The number of knots inserted into each segment is proportional to
    the span of curve's T parameter, corresponding to the segment.
  * **Distribute Length**. New knots are inserted into each segment between
    existing curve knots, distributed evenly (according to curve arc length)
    inside each segment. The number of knots inserted into each segment is
    proportional to the curve arc length within the segment.
  * **Bisect T**. New knot is inserted in the middle (in curve's parameter
    space) of the segment between existing curve knots, which has the maximum
    span of curve's T parameter; thus, this segment is subdivided in two
    smaller ones. The following knot is similarly inserted into the segment
    which is now largest. The procedure is repeated until the required number
    of knots is inserted.
  * **Bisect Length**. New knot is inserted in the middle (in terms of curve arc
    length) of the segment between existing curve knots, which has the maximum
    curve arc length; thus, this segment is subdivided in two smaller ones. The
    following knot is similarly inserted into the segment which is now largest.
    The procedure is repeated until the required number of knots is inserted.

* **Insert each knot**. This defines the number of times each knot is inserted. The available options are:

  * **Once**. Each knot is inserted one time.
  * **As possible**. Each knot is inserted as many times as possible; that is,
    `p-1` times, where `p` is the degree of the curve - if the new knot does
    not coincide with any of existing knots; or smaller number of times, if the
    new knot happens to coincide with previously existing knot. This option is
    the default.

* **Specify Segment**. If checked, the node allows you to specify the range of
  curve's T parameter, into which all new knots are inserted. The range is
  specified by **TMin**, **TMax** inputs. If the parameter is not checked, then
  new knots will be inserted along the whole curve. Unchecked by default.

Outputs
-------

This node has the following outputs:

* **Curve**. The resulting NURBS Curve object.
* **NewKnots**. The values of newly inserted knots.

Example of Usage
----------------

Black curve is the original one. Cyan / blue is the control polygon of the original curve. Dark blue points on the curve indicate the knot values of original curve.

Red lines with orange dots indicate the control polygon of the resulting curve. Green dots indicate the newly inserted knots.

As you can see, inserting 10 knots creates a lot of control points.

.. image:: https://user-images.githubusercontent.com/284644/185967665-5105d75c-5fd4-496a-9664-b81322b8e24d.png

