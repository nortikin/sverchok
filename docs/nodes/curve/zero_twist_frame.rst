Curve Zero-Twist Frame
======================

Functionality
-------------

This node calculates a reference frame along the curve, which has minimal
rotation around curve's tangent while moving along the curve. Such a frame is
calculated by rotating curve's Frenet_ frame around curve's tangent (in the
negative direction). More precisely, an indefinite integral of curve's torsion_
is calculated to get the total rotation of Frenet frame around the tangent
while moving from curve's starting point to any other point.

The indefinite integral is calculated numerically, by subdividing the domain of
the curve in many pieces. The more pieces are used, the more precise the
calculation will be, but the more time it will take. So, this node allows one
to specify the number of curve subdivisions to be used.

.. _Frenet: https://en.wikipedia.org/wiki/Frenet%E2%80%93Serret_formulas
.. _torsion: https://en.wikipedia.org/wiki/Torsion_of_a_curve

Inputs
------

This node has the following inputs:

* **Curve**. The curve to calculate frame for. This input is mandatory.
* **Resolution**. The number of segments to subdivide the curve in to calculate the torsion integral. The bigger the value is, the more precise calculation will be, but the more time it will take. The default value is 50.
* **T**. The value of curve's T parameter to calculate the frame at. The default value is 0.5.

Parameters
----------

This node has the following parameter:

* **Join**. If checked, the node will output the single list of matrices,
  joined from any number of input curves provided. Otherwise, the node will
  output a separate list of matrices for each input curve. Checked by default.

Outputs
-------

This node has the following outputs:

* **CumulativeTorsion**. Total angle of curve's Frenet frame rotation around
  curve's tangent, when moving from curve's starting point to the specified T
  parameter value — i.e., the indefinite integral of curve's torsion. The angle
  is expressed in radians.
* **Matrix**. Curve's zero-twist frame at specified value of the T parameter.
  The location component of the matrix is the point of the curve. Z axis of the
  matrix points along curve's tangent.

Example of usage
----------------

Use zero-twist frames to put cubes along the curve:

.. image:: https://user-images.githubusercontent.com/284644/78504364-20edcd80-7786-11ea-831e-80db9be81e2b.png

Compare that to the use of curve's Frenet frames:

.. image:: https://user-images.githubusercontent.com/284644/78504337-ed12a800-7785-11ea-9a6c-1427ced45d55.png

