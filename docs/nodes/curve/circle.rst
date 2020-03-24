Circle (Curve)
==============

Funcitonality
-------------

This node generates a Curve object, which represents a circle, or an arc of the circle.

Specifics of curve parametrization: the T parameter is proportional to curve
length, and equals to the angle along the circle arc.

Curve domain: defined in node's inputs, by default from 0 to 2*pi.

Behavior when trying to evaluate curve outside of it's boundaries: returns
corresponding point on the circle.

Inputs
------

This node has the following inputs:

* **Center**. A matrix defining the location of the circle. This may be used to
  move, scale or rotate the curve. By default, the center of matrix is at the
  origin, and the circle is laying in the XOY plane.
* **Radius**. Circle radius. The default value is 1.0.
* **T Min**. Minimum value of the curve parameter. The default value is 0.0.
* **T Max**. Maximum value of the curve parameter. The default value is 2*pi.

Parameters
----------

This node does not have parameters.

Outputs
-------

This node has one output:

* **Curve**. The circle (or arc) curve.

Examples of usage
-----------------

Simple use:

.. image:: https://user-images.githubusercontent.com/284644/77347101-27794f80-6d59-11ea-9bcd-182c918222cc.png

Use together with Extrude node to create a surafce:

.. image:: https://user-images.githubusercontent.com/284644/77347798-344a7300-6d5a-11ea-88c2-e25e12be74b9.png

