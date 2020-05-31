Kinked Curve
============

Functionality
-------------

This node generates a "kinky" curve, i.e. a curve that is smooth in some places
and sharp in others. The node allows the ability to control a specific angle
threshold where the curve will transition from a kinked line to a smooth
interpolated curve.

This node calculates angles between consequent segments of a polyline built
from original points; if the angle at a point is less than specified threshold,
the curve will have sharp angle at this point; otherwise, the curve will be
smooth.

The node generates a separate Curve object for each smooth segment of a curve;
these segments can be optionally concatenated into one Curve object.

Inputs
------

This node has the following inputs:

* **Vertices**. The vertices to interpolate between. This input is mandatory.
* **AngleThreshold**. Threshold of the angle between points, which defines at
  which points the curve will have sharp corners. The value is expected in
  radians. The default value is ``pi/6``.

Parameters
----------

This node has the following parameters:

* **Concatenate**. If checked, the node will output single Curve object for
  each set of points. Otherwise, it will generate a separate Curve object for
  each smooth segment of the curve. Checked by default.
* **Cyclic**. If checked, the node will generate a cyclic (closed) curve.
  Unchecked by default.
* **Metric**. This parameter is available in the N panel only. This defines the
  metric used to calculate curve's T parameter values corresponding to
  specified curve points. The available values are:

   * Manhattan
   * Euclidian
   * Points (just number of points from the beginning)
   * Chebyshev.

   The default value is Euclidian.

Outputs
-------

This node has the following output:

* **Curve**. Generated curve object(s).

Examples of usage
-----------------

A simple example:

.. image:: https://user-images.githubusercontent.com/284644/83358403-a956ac00-a38c-11ea-9619-00af2e93b613.png

Similar example with a closed curve:

.. image:: https://user-images.githubusercontent.com/284644/83358400-a8257f00-a38c-11ea-88ba-530ccc1742fd.png

