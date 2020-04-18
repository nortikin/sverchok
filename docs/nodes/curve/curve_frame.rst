Curve Frame
===========

Functionaltiy
-------------

This node calculates a reference frame of a curve (also known as Frenet_ frame)
for the given value of curve's T parameter. Basically, the node allowes one to
place some object at the curve, by aligning the object with curve's "natural"
orientation.

.. _Frenet: https://en.wikipedia.org/wiki/Frenet%E2%80%93Serret_formulas

Note that Frenet frame of the curve rotates along curve's tangent according to
curve's own torsion. Thus, if you place something by this frame, the result can
be somewhat twisted. If you want to minimize the twist, you may wish to use
**Zero-Twist Frame** node.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to calculate frame for. This input is mandatory.
* **T**. The value of curve's T parameter. The default value is 0.5.

Parameters
----------

This node has the following parameter:

* **Join**. If checked, the node will output the single list of matrices,
  joined from any number of input curves provided. Otherwise, the node will
  output a separate list of matrices for each input curve. Checked by default.

Outputs
-------

This node has the following outputs:

* **Matrix**. The matrix defining the Frenet frame for the curve at the specified value of T parameter. The location component of the matrix is the point of the curve. Z axis of the matrix points along curve's tangent.
* **Normal**. The direction of curve's main normal at the specified value of T parameter.
* **Binormal**. The direction of curve's binormal at the specified value of T parameter.

Examples of usage
-----------------

Visualize curve's frame at some points:

.. image:: https://user-images.githubusercontent.com/284644/78504334-eb48e480-7785-11ea-81cb-6987e67830b0.png

Use these frames to put cubes along the curve, aligning them along curve's natural orientation:

.. image:: https://user-images.githubusercontent.com/284644/78504337-ed12a800-7785-11ea-9a6c-1427ced45d55.png

